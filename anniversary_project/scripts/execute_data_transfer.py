import time

from django.db.models.query import QuerySet
from s3connections.models import S3Connection
from .s3portal.portal_utils import get_active_conn, get_scheduled_jobs, initialize_job_queue


HEARTBEAT = 10


def run():
    active_conn: S3Connection = get_active_conn()
    scheduled_jobs: QuerySet = get_scheduled_jobs()

    #   If there is no active connection or no job to execute, then print appropriate message and sleep for
    #   a cycle
    if (not active_conn) or (len(scheduled_jobs) == 0):
        print("No active connection found" if (not active_conn) else "No scheduled jobs found")
    else:
        job_queue = initialize_job_queue(active_conn, scheduled_jobs)
        print(f"{len(job_queue)} jobs found")
        for job in job_queue:
            job.execute()
