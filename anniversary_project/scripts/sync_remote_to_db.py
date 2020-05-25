import time
import typing as ty
import os

from botocore.errorfactory import ClientError

from archive.models import Archive, ArchivePartMeta, PersistentTransferJob
from s3connections.models import S3Connection
from .s3portal.portal_utils import get_active_conn


HEARTBEAT = 10


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


def queue_upload(archive_part_meta: ArchivePartMeta) -> bool:
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


def run():
    """
    If there is no active connection, then sleep for 10 seconds.
    If there is an active connection, then iterate through all archive part instances:
    """
    while True:
        active_conn = get_active_conn()
        if not active_conn:
            print(f"No active connection found; sleep until next cycle")
        for archive_part_meta in ArchivePartMeta.objects.all():
            archive_part_meta: ArchivePartMeta = archive_part_meta
            if has_healthy_remote(archive_part_meta, active_conn):
                archive_part_meta.uploaded = True
                archive_part_meta.save()
            else:
                if has_remote(archive_part_meta, active_conn):
                    remove_remote(archive_part_meta, active_conn)
                archive_part_meta.uploaded = False
                archive_part_meta.save()
                if has_local_file(archive_part_meta):
                    queue_upload(archive_part_meta)

        time.sleep(HEARTBEAT)

