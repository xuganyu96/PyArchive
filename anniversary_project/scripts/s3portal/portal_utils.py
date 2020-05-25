from typing import Optional, Iterable

from django.db.models.query import QuerySet

from anniversary_project.settings import MEDIA_ROOT
from s3connections.models import S3Connection
from archive.models import PersistentTransferJob
from .data_transfer_job import DataUploadJob, DataDownloadJob, DataTransferJob


def get_active_conn() -> Optional[S3Connection]:
    """
    :return: among all objects of S3Connection.objects, take the first one with is_active. If no connection is
    active, then return None and print message
    """
    active_conns = S3Connection.objects.filter(is_active=True)
    if len(active_conns) == 0:
        return None
    else:
        return active_conns.first()


def get_scheduled_jobs() -> Optional[QuerySet]:
    """
    :return: return all objects in PersistentTransferJob whose status is 'scheduled'. If no jobs are found,
    return empty QuerySet
    """
    return PersistentTransferJob.objects.filter(status='scheduled')


def initialize_job_queue(active_conn: S3Connection,
                         scheduled_jobs: Iterable[PersistentTransferJob]) -> Iterable[DataTransferJob]:
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
