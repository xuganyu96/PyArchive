import os
import time
from typing import Optional, Iterable

from boto3.session import Session
import django
from django.db.models.query import QuerySet
from django.utils import timezone

from anniversary_project.settings import MEDIA_ROOT
from s3connections.models import S3Connection
from archive.models import PersistentTransferJob
from .data_transfer_job import DataUploadJob, DataDownloadJob, DataTransferJob


def main(heart_beat: int = 10):
    """
    :param heart_beat: the number of seconds to stay idle for, for each empty cycle
    If there is no active connections available, then do an empty cycle
    If there is, then look inside PersistentTransferJob:
        1.  Find all instances whose statuses are "scheduled"
        2.  For each of those instances:
            1.  get: owner's username, archive_id, file_part_index, start_byte_index, end_byte_index
            2.  get: anniversary_project.settings.MEDIA_ROOT
            3.  Use MEDIA_ROOT and instance.archive.archive_file.name to construct the full path to the archive file
                then read the file part using start_byte_index and end_byte_index
            4.  Do a S3 upload with path:
                s3://connection_id/username/archive_id/file_part_index
    """
    while True:
        active_conn: S3Connection = get_active_conn()
        scheduled_jobs: QuerySet = get_scheduled_jobs()

        #   If there is no active connection or there is no job to execute, then print respective message
        #   and sleep for a cycle
        if (not active_conn) or (len(scheduled_jobs) == 0):
            print("No active connection found" if (not active_conn) else "No scheduled jobs found")
            print(f"Sleep for {heart_beat} seconds")
            time.sleep(heart_beat)
        else:
            #   There is an active connection and there are one or more scheduled jobs
            job_queue = initialize_job_queue(active_conn, scheduled_jobs)
            print(f"{len(job_queue)} jobs found")
            for job in job_queue:
                job.execute()


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


if __name__ == '__main__':
    main()
