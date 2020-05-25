import typing as ty
import os

from django.db.models.query import QuerySet
from botocore.errorfactory import ClientError

from anniversary_project.settings import MEDIA_ROOT
from s3connections.models import S3Connection
from archive.models import Archive, ArchivePartMeta, PersistentTransferJob
from .data_transfer_job import DataUploadJob, DataDownloadJob, DataTransferJob


def get_active_conn() -> ty.Optional[S3Connection]:
    """
    :return: among all objects of S3Connection.objects, take the first one with is_active. If no connection is
    active, then return None and print message
    """
    active_conns = S3Connection.objects.filter(is_active=True)
    if len(active_conns) == 0:
        return None
    else:
        return active_conns.first()


def get_scheduled_jobs() -> ty.Optional[QuerySet]:
    """
    :return: return all objects in PersistentTransferJob whose status is 'scheduled'. If no jobs are found,
    return empty QuerySet
    """
    return PersistentTransferJob.objects.filter(status='scheduled')


def initialize_job_queue(active_conn: S3Connection,
                         scheduled_jobs: ty.Iterable[PersistentTransferJob]) -> ty.Iterable[DataTransferJob]:
    """
    :param active_conn: an S3Connectin object whose .is_active is True
    :param scheduled_jobs: QuerySet of PersistentTransferJob objects
    :return: Scan through the QuerySet and for each one of the scheduled jobs, instantiate the appropriate
    DataTransferJob and put it in a list
    """
    job_queue = list()
    for scheduled_job in scheduled_jobs:
        if scheduled_job.transfer_type == 'upload':
            job_queue.append(DataUploadJob(conn=active_conn, job_meta=scheduled_job))
        elif scheduled_job.transfer_type == 'download':
            job_queue.append(DataDownloadJob(conn=active_conn, job_meta=scheduled_job))
        else:
            print(f"job {scheduled_job.pk} is neither upload nor download")

    return job_queue


def has_remote(archive_part_meta: ArchivePartMeta, active_conn: S3Connection) -> bool:
    """
    :param archive_part_meta:
    :param active_conn:
    :return: return True if and only if the corresponding remote part exists
    """
    username = archive_part_meta.archive.owner.username
    archive_id = archive_part_meta.archive.archive_id
    part_index = archive_part_meta.part_index
    file_key = f"{username}/{archive_id}/{part_index}"
    s3 = active_conn.get_client('s3')
    try:
        response = s3.head_object(Bucket=active_conn.connection_id,
                                  Key=file_key)
        return True
    except ClientError as ce:
        return False


def remove_remote(archive_part_meta: ArchivePartMeta, active_conn: S3Connection) -> bool:
    """
    :param archive_part_meta:
    :param active_conn:
    :return: return the file key if the deletion if successful
    """
    username = archive_part_meta.archive.owner.username
    archive_id = archive_part_meta.archive.archive_id
    part_index = archive_part_meta.part_index
    file_key = f"{username}/{archive_id}/{part_index}"
    s3 = active_conn.get_client('s3')
    try:
        response = s3.head_object(Bucket=active_conn.connection_id,
                                  Key=file_key)
        #   ETag is wrapped in double quotes
        remote_checksum = response['ETag'][1:-1]
        response = s3.delete_object(Bucket=active_conn.connection_id,
                                    Key=file_key)
        #   DELETE!
    except ClientError as ce:
        return False


def get_remote_checksum(archive_part_meta: ArchivePartMeta, active_conn: S3Connection) -> ty.Optional[str]:
    """
    :param archive_part_meta:
    :param active_conn:
    :return: the ETag (checksum) of the corresponding file if the remote exists; otherwise, return None
    """
    username = archive_part_meta.archive.owner.username
    archive_id = archive_part_meta.archive.archive_id
    part_index = archive_part_meta.part_index
    file_key = f"{username}/{archive_id}/{part_index}"
    s3 = active_conn.get_client('s3')
    try:
        response = s3.head_object(Bucket=active_conn.connection_id,
                                  Key=file_key)
        #   ETag is wrapped in double quotes
        remote_checksum = response['ETag'][1:-1]
        return remote_checksum
    except ClientError as ce:
        print("Response is bad")
        return None


def has_healthy_remote(archive_part_meta: ArchivePartMeta, active_conn: S3Connection) -> bool:
    """
    :param archive_part_meta:
    :param active_conn:
    :return: True if and only if the corresponding remote part exists, and the checksums match
    """
    if not has_remote(archive_part_meta, active_conn):
        return False
    else:
        remote_checksum = get_remote_checksum(archive_part_meta, active_conn)
        db_checksum = archive_part_meta.part_checksum
        checksums_match = (db_checksum == remote_checksum)
        return checksums_match


def has_local_file(archive_part_meta: ArchivePartMeta) -> bool:
    """
    :param archive_part_meta:
    :return: True if and only if the the archive's complete file exists locally
    """
    archive_file_path = archive_part_meta.archive.archive_file.file.name
    return os.path.exists(archive_file_path) and os.path.isfile(archive_file_path)


def queue_upload(archive_part_meta: ArchivePartMeta):
    """
    :param archive_part_meta:
    :return: assuming that the archive file exists, create a number of upload jobs if they don't already
    exist
    """
    #   First check if upload job of this archive_part_meta already exists
    existing_job = PersistentTransferJob.objects.filter(content_meta=archive_part_meta,
                                                        status='scheduled')
    if len(existing_job) == 0:
        #   If the QuerySet above is empty, then schedule a new job
        upload_job = PersistentTransferJob(content_meta=archive_part_meta,
                                           transfer_type='upload',
                                           status='scheduled')
        upload_job.save()
        print(f"Queued job: {upload_job}")
