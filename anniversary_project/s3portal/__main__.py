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
from archive.models import PersistentTransferJob


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
        time.sleep(heart_beat)


if __name__ == '__main__':
    main()