import os
import time

from boto3.session import Session
import django
from django.db.models.query import QuerySet
from django.utils import timezone
from django.conf import settings

#   You need to set up project settings before being able to access models within Django Apps outside Django
from anniversary_project.settings import DATABASES, INSTALLED_APPS
settings.configure(DATABASES=DATABASES, INSTALLED_APPS=INSTALLED_APPS)
django.setup()
from anniversary_project.settings import MEDIA_ROOT
from s3connections.models import S3Connection
from archive.models import PersistentFileTransfer


def main(heart_beat: int = 10):
    """
    :param heart_beat: the number of seconds to stay idle for, for each empty cycle
    If there is no active connections available, then do an empty cycle
    If there is, then look inside PersistentFileTransfer:
        1.  Find all instances whose statuses are "scheduled"
        2.  For each of those instances:
            1.  get: owner's username, archive_id, file_part_index, start_byte_index, end_byte_index
            2.  get: anniversary_project.settings.MEDIA_ROOT
            3.  Use MEDIA_ROOT and instance.archive.archive_file.name to construct the full path to the archive file
                then read the file part using start_byte_index and end_byte_index
            4.  Do a S3 upload with path:
                s3://connection_id/username/archive_id/file_part_index.fpart
    """
    while True:
        active_conn = S3Connection.objects.filter(is_active=True).first()
        jobs_in_queue: QuerySet = PersistentFileTransfer.objects.filter(status='scheduled')
        if not active_conn or len(jobs_in_queue) == 0:
            time.sleep(heart_beat)
        else:
            print(f"Active connection found with bucket name {active_conn.connection_id}")
            #   There exists active connection and there are unfinished jobs
            print(f"{len(jobs_in_queue)} unfinished file transfer jobs found")
            for job in jobs_in_queue:
                username = job.archive.owner.username
                archive_id = job.archive.archive_id
                file_part_index = job.file_part_index
                start_byte_index = job.start_byte_index
                end_byte_index = job.end_byte_index
                file_full_path = os.path.join(MEDIA_ROOT, job.archive.archive_file.name)
                with open(file_full_path, 'rb') as f:
                    f.seek(start_byte_index)
                    file_part = f.read(end_byte_index - start_byte_index)

                job.date_started = timezone.now()
                job.save()
                try:
                    upload_file_part(active_conn, username, archive_id, file_part_index, file_part)
                    print(f"{job.batch_id} of size {job.end_byte_index - job.start_byte_index} bytes uploaded")
                    job.status = 'completed'
                    job.date_completed = timezone.now()
                    job.save()
                except Exception as e:
                    print(e)


def upload_file_part(conn: S3Connection, username: str, archive_id: str, file_part_index: int, file_part: bytes):
    """
    :param conn:
    :param username:
    :param archive_id:
    :param file_part_index:
    :param file_part:
    :return:
    """
    s3 = Session(aws_access_key_id=conn.access_key,
                 aws_secret_access_key=conn.secret_key,
                 region_name=conn.region_name).client('s3')
    response = s3.put_object(Body=file_part,
                             Bucket=conn.connection_id,
                             Key=f"{username}/{archive_id}/{file_part_index}")

    return response


if __name__ == '__main__':
    main()