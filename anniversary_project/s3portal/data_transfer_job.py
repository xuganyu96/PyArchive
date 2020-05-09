import os
import abc
import shutil

from boto3.session import Session
from botocore.errorfactory import ClientError
import django
from django.db.models.query import QuerySet
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User

from anniversary_project.settings import MEDIA_ROOT
from s3connections.models import S3Connection
from s3connections.utils import is_valid_connection_credentials
from archive.models import PersistentTransferJob

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
        self.s3 = self.get_s3_client(self.conn)

    @classmethod
    def get_s3_client(cls, conn: S3Connection):
        """
        :param conn: an S3Connection object
        :return: a boto3 s3 client
        """
        assert conn.is_valid
        assert conn.is_active

        session = Session(aws_access_key_id=conn.access_key,
                          aws_secret_access_key=conn.secret_key,
                          region_name=conn.region_name)
        s3 = session.client('s3')
        return s3

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
            except Exception as e:
                return False

        #   Check remote conditions
        username = self.job_meta.content_meta.archive.owner.username
        archive_id = self.job_meta.content_meta.archive.archive_id
        validation_s3_key = f"{username}/{archive_id}/hello_world"

        try:
            response = self.s3.put_object(Body=b"Hello World",
                                          Bucket=self.conn.connection_id,
                                          Key=validation_s3_key)
            response = self.s3.delete_object(Bucket=self.conn.connection_id,
                                             Key=validation_s3_key)
        except Exception as e:
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
        try:
            self.s3.put_object(Body=content,
                               Bucket=self.conn.connection_id,
                               Key=s3_key)
            self.job_meta.status = 'completed'
            self.job_meta.content_meta.uploaded = True
            self.job_meta.date_completed = timezone.now()
            self.job_meta.save()
            self.job_meta.content_meta.save()
            print(f"{self.__str__()} was successful!")
        except Exception as e:
            print(e)


class DataDownloadJob(DataTransferJob):

    def _get_bucket_name(self) -> str:
        return self.conn.connection_id

    # {username}/{archive_id}/{part_index}
    def _get_file_key(self) -> str:
        username = self.job_meta.content_meta.archive.owner.username
        archive_id = self.job_meta.content_meta.archive.archive_id
        part_index = self.job_meta.content_meta.part_index

        return f"{username}/{archive_id}/{part_index}"

    @classmethod
    def _make_dest_dir(cls, dest):
        """
        :param dest: path to the destination of the file download
        :return: if the hosting directory doesn't exist, then create it
        """
        dest_dir = os.path.split(dest)[0]
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

    def get_source(self) -> str:
        """
        :return: the source of a data download job is the full S3 path including the bucket name and the id
        """
        return f"s3://{self._get_bucket_name()}/{self._get_file_key()}"

    def get_dest(self) -> str:
        """
        :return: the destination is as follows:
        MEDIA_ROOT/cache/username/archive_id/part_index
        """
        cache_relative_dir = f"cache/{self._get_file_key()}"
        return os.path.join(MEDIA_ROOT, cache_relative_dir)

    def is_valid_job(self) -> bool:
        """
        :return: a download job is valid if and only if all of the conditions below are satisfied:
        -   self.connection is valid and active
        -   the S3 bucket and key combination can be used to grab a valid "head" object
        -   the file part checksum is consistent
        """
        if not (self.conn.is_active and self.conn.is_valid):
            return False
        else:
            bucket_name = self._get_bucket_name()
            file_key = self._get_file_key()

            try:
                obj_header = self.s3.head_object(
                    Bucket=bucket_name,
                    Key=file_key
                )
                remote_checksum = obj_header['ETag'][1:-1]
                if self.job_meta.content_meta.part_checksum != remote_checksum:
                    return False
            except ClientError as ce:
                return False

    def execute(self):
        """
        Download the file part and store it in the right place
        """
        dest = self.get_dest()
        self._make_dest_dir(dest)

        bucket_name = self._get_bucket_name()
        file_key = self._get_file_key()

        self.job_meta.date_started = timezone.now()
        self.job_meta.save()
        try:
            self.s3.download_file(Bucket=bucket_name,
                                  Key=file_key,
                                  Filename=dest)
            self.job_meta.status = 'completed'
            self.job_meta.content_meta.cached = True
            self.job_meta.date_completed = timezone.now()
            self.job_meta.save()
            self.job_meta.content_meta.save()
            print(f"{self.__str__()} was successful!")
        except ClientError as ce:
            print(ce)
