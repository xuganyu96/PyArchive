import abc
import os
import shutil
import time
from typing import Optional, Iterable

from boto3.session import Session
import django
from django.db.models.query import QuerySet
from django.utils import timezone
from django.contrib.auth.models import User

from anniversary_project.settings import MEDIA_ROOT
from s3connections.models import S3Connection
from archive.models import Archive, ArchivePartMeta, PersistentTransferJob
from archive.forms import ArchiveForm
from .data_transfer_job import DataUploadJob, DataDownloadJob, DataTransferJob
from .daemon_actions import get_active_conn, get_scheduled_jobs, initialize_job_queue


class HouseChore(abc.ABC):
    """
    The abstract class for defining a house chore instance. All house chore instances will be executed as part of a
    local house keeping routine
    """
    @abc.abstractmethod
    def execute(self):
        raise NotImplementedError('execution not defined')

    @abc.abstractmethod
    def description(self):
        raise NotImplementedError('house chore name not defined')


class SyncLocalCacheWithLocalArchive(HouseChore):
    @classmethod
    def check_cache_health(cls, archive_cache_dir: str, archive_id: str) -> bool:
        """
        :param archive_cache_dir: an archive's cache directory
        :param archive_id:
        :return: True if and only if the all parts are present and are in good health
        """
        archive = Archive.objects.get(pk=archive_id)
        archive_parts_meta = ArchivePartMeta.objects.filter(archive=archive)
        ready_for_assembly = True
        for archive_part_meta in archive_parts_meta:
            cache_part_file_path = os.path.join(archive_cache_dir, str(archive_part_meta.part_index))
            if not (os.path.exists(cache_part_file_path) and os.path.isfile(cache_part_file_path)):
                #   If the desired path doesn't point to an existing file, then the archive is not ready for assembly
                ready_for_assembly = False
            else:
                cache_part_file_checksum = ArchiveForm.get_file_checksum(file_path=cache_part_file_path)
                if cache_part_file_checksum != archive_part_meta.part_checksum:
                    #   If the file part's checksum does not check out, then remove the file part
                    print(f"Corrupted file part at {cache_part_file_path}")
                    os.remove(cache_part_file_path)
                    archive_part_meta.cached = False
                else:
                    archive_part_meta.cached = True
                archive_part_meta.save()

        return ready_for_assembly

    @classmethod
    def assemble_archive(cls, username, archive_id):
        """
        :param username:
        :param archive_id:
        :return: read in the parts in cache directory and write all bytes in a single swoop to the archive directory
        """
        cache_dir = os.path.join(MEDIA_ROOT, 'cache', username, archive_id)
        archive_dir = os.path.join(MEDIA_ROOT, 'archives', username, archive_id)
        #   Delete archive_dir and remake it
        shutil.rmtree(path=archive_dir)
        os.makedirs(archive_dir)
        #   Sort the file parts numerically by the index
        file_part_names = os.listdir(cache_dir)
        file_part_names.sort(key=lambda x: int(x))
        #   Find the original file name
        archive: Archive = Archive.objects.get(pk=archive_id)
        archive_file_name = os.path.basename(archive.archive_file.name)
        archive_file_path = os.path.join(archive_dir, archive_file_name)
        #   Start writing in batches:
        with open(archive_file_path, 'ab') as f:
            for file_part_name in file_part_names:
                file_part_path = os.path.join(cache_dir, file_part_name)
                with open(file_part_path, 'rb') as p:
                    f.write(p.read())
        #   Confirm the checksum
        written_checksum = ArchiveForm.get_file_checksum(file_path=archive_file_path)
        if written_checksum == archive.archive_file_checksum:
            print(f"Successfully assembled archive at {archive_file_path}")
            archive.cached = True
            archive.save()
            shutil.rmtree(cache_dir)
        else:
            print(f"Oh oh something went wrong")

    def execute(self):
        """
        Check integrity of local cache and assemble them into complete archive if all of them are in good health
        """
        cache_dir = os.path.join(MEDIA_ROOT, 'cache')
        for username in os.listdir(cache_dir):
            user_cache_dir = os.path.join(cache_dir, username)
            for archive_id in os.listdir(user_cache_dir):
                archive_cache_dir = os.path.join(user_cache_dir, archive_id)
                ready_for_assembly = self.check_cache_health(archive_cache_dir, archive_id)
                if ready_for_assembly:
                    self.assemble_archive(username, archive_id)

    def description(self):
        return 'Synchronize among local cache directory, local archive directory, and the relevant DB instances'


def clean_the_house():
    print(f"{SyncLocalCacheWithLocalArchive().description()}")
    SyncLocalCacheWithLocalArchive().execute()
