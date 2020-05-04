import os
import abc

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
from s3connections.utils import is_valid_connection_credentials
from archive.models import PersistentTransferJob

from .callbacks import DownloadProgressPercentage, UploadProgressPercentage
"""
# The `DataTransferJob` class
This will be an abstract class that the `DataUploadJob` and the `DataDownloadJob` need to implement. Things that are 
common between an upload and a download:
1. A `get_source()` instance method
2. A `get_destination()` instance method
3. A `check_connection()` instance method
4. A `execute()` instance method
"""


class DataTransferJob(abc.ABC):

    def __init__(self, conn: S3Connection, job_meta: PersistentTransferJob):
        self.conn = conn
        self.job_meta = job_meta

    @abc.abstractmethod
    def get_source(self) -> str:
        """
        :return: a string that is either an S3 URL like s3://connection_id/username/archive_id/part_index or a local
        path to the archive file with byte indexing like
        /media/archives/username/archive_id/file.ext[start:end]
        """
        raise NotImplementedError('get_source is not implemented')

    @abc.abstractmethod
    def get_dest(self) -> str:
        """
        :return: similar things to get_source except for that it is the destination
        """
        raise NotImplementedError('get_dest is not implemented')

    @abc.abstractmethod
    def is_valid_job(self) -> bool:
        """
        :return: return True if and only if the job can be executed (if no outage occurs), but don't do the job yet
        """

    @abc.abstractmethod
    def execute(self):
        raise NotImplementedError('execute is not implemented')

    def __str__(self):
        source = self.get_source()
        dest = self.get_dest()

        return f"Transferring from {source} to {dest}"


class DataUploadJob(DataTransferJob):

    def get_source(self) -> str:
        """
        :return: absolute path to the archive file, then followed by byte index slicing
        """
        abs_path = os.path.join(MEDIA_ROOT, self.job_meta.content_meta.archive.archive_file.name)
        start_byte = self.job_meta.content_meta.start_byte_index
        end_byte = self.job_meta.content_meta.end_byte_index
        return f"{abs_path}::[{start_byte}:{end_byte}]"

    def get_dest(self) -> str:
        """
        :return: s3 path to the
        """
        bucket_id = self.conn.connection_id
        username = self.job_meta.content_meta.archive.owner.username
        archive_id = self.job_meta.content_meta.archive.archive_id
        part_index = self.job_meta.content_meta.part_index
        return f"s3://{bucket_id}/{username}/{archive_id}/{part_index}"

    def is_valid_job(self) -> bool:
        """
        :return: True if and only if all of the following conditions are satisfied:
        -   local file exists
        -   local file's byte sequence can be read in
        -   bucket exists
        -   Attempt to upload 'hello world' into that bucket, and the upload can succeed
        """
        abs_path = os.path.join(MEDIA_ROOT, self.job_meta.content_meta.archive.archive_file.name)
        start_byte = self.job_meta.content_meta.start_byte_index
        end_byte = self.job_meta.content_meta.end_byte_index

        #   Check local conditions
        if not os.path.isfile(abs_path):
            return False
        else:
            try:
                with open(abs_path, 'rb') as f:
                    f.seek(start_byte)
                    f.read(end_byte - start_byte)
            except:
                return False

        #   Check remote conditions
        username = self.job_meta.content_meta.archive.owner.username
        archive_id = self.job_meta.content_meta.archive.archive_id
        validation_s3_key = f"{username}/{archive_id}/hello_world"
        s3 = Session(aws_access_key_id=self.conn.access_key,
                     aws_secret_access_key=self.conn.secret_key,
                     region_name=self.conn.region_name).client('s3')
        try:
            response = s3.put_object(Body=b"Hello World",
                                     Bucket=self.conn.connection_id,
                                     Key=validation_s3_key)
            response = s3.delete_object(Bucket=self.conn.connection_id,
                                        Key=validation_s3_key)
        except:
            return False

        return True

    def execute(self):
        """
        :return: grab the local file, read its byte sequence, upload it to the S3 bucket with correct path, and return
        the full path.
        """
        #   A bit of prep work for gathering arguments
        abs_path = os.path.join(MEDIA_ROOT, self.job_meta.content_meta.archive.archive_file.name)
        start_byte = self.job_meta.content_meta.start_byte_index
        end_byte = self.job_meta.content_meta.end_byte_index
        with open(abs_path, 'rb') as f:
            f.seek(start_byte)
            content = f.read(end_byte - start_byte)
        username = self.job_meta.content_meta.archive.owner.username
        archive_id = self.job_meta.content_meta.archive.archive_id
        part_index = self.job_meta.content_meta.part_index
        s3_key = f"{username}/{archive_id}/{part_index}"

        #   let's go!
        self.job_meta.date_started = timezone.now()
        self.job_meta.save()
        s3 = Session(aws_access_key_id=self.conn.access_key,
                     aws_secret_access_key=self.conn.secret_key,
                     region_name=self.conn.region_name).client('s3')
        s3.put_object(Body=content,
                      Bucket=self.conn.connection_id,
                      Key=s3_key)




