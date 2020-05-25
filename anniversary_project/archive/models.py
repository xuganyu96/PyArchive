import uuid
import os
import shutil
import typing as ty
import hashlib

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse

from anniversary_project.settings import MEDIA_ROOT


def archive_file_save_path(instance, filename) -> str:
    """
    :param instance: an Archive instance
    :param filename: the name of the file when it was uploaded
    :return: the path to which the file will be saved (under MEDIA_ROOT directory)
    """
    return f"archives/{instance.owner.username}/{instance.archive_id}/{filename}"


def get_file_checksum(file_path, hash_func=hashlib.md5, chunk_size=8192) -> str:
    """
        :param file_path:
        :param hash_func:
        :param chunk_size:
        :return: the checksum of the file using the hashing function. Read in chunks to preserve RAM
        """
    with open(file_path, "rb") as f:
        file_hash = hash_func()
        remains = f.read(chunk_size)
        while remains:
            file_hash.update(remains)
            remains = f.read(chunk_size)

    return file_hash.hexdigest()


class Archive(models.Model):
    """
    Abstraction of the an archive. Each archive corresponds to a file (possibly not distinct).
    -   archive_id:
    -   archive_file:
    -   archive_name:
        a user specified name for the archive, like "My Favorite Movies"
    -   owner:
        the User who created this archive, and who is the only one allowed to view, edit, and download this archive
    -   date_created:
        the datetime (of local timezone) at which this archive instance is uploaded and created
    -   cached:
        True if and only if the archive_file exists in its original place
    """

    archive_id = models.CharField(max_length=64, default=uuid.uuid4, primary_key=True)
    archive_name = models.CharField(max_length=512, null=True)
    archive_file = models.FileField(upload_to=archive_file_save_path)
    archive_file_checksum = models.CharField(max_length=32, null=True)
    owner: User = models.ForeignKey(to=User, on_delete=models.CASCADE)
    date_created = models.DateTimeField(default=timezone.now)
    cached = models.BooleanField(default=True, null=False)

    def __str__(self):
        return self.archive_id + " owned by " + self.owner.username

    #   Define the method for returning the URL of specific archive's detail page
    def get_absolute_url(self):
        return reverse("archive-detail", kwargs={"pk": self.archive_id})

    def delete(self, using=None, keep_parents=False):
        """
        Overwrite the default delete method so the file would be deleted when the model instance is deleted
        """
        #   Don't for get about deleting the directory immediately containing the file, as well
        abs_path = os.path.join(MEDIA_ROOT, self.archive_file.name)
        wrapper_dir_path = os.path.split(abs_path)[0]
        self.archive_file.storage.delete(self.archive_file.name)
        shutil.rmtree(wrapper_dir_path)
        super().delete()

    def get_local_checksum(self) -> ty.Optional[str]:
        """
        if local file exists, then return its checksum as a string; otherwise, return None
        """
        archive_file_path = self.archive_file.file.name
        if os.path.exists(archive_file_path) and os.path.isfile(archive_file_path):
            return get_file_checksum(file_path=archive_file_path)
        else:
            return None


class ArchivePartMeta(models.Model):
    """
    Abstraction of an Archive file's file parts with their precise start and end byte index
    -   uploaded:
        True if and only if this sequence of bytes have been uploaded onto AWS S3
    -   cached:
        True if and only if this sequence of bytes exist in the cache folder in the correct subdirectory
        Note that whether the archive is cached is entirely independent of whether specific archive part is cached;
        the two things live in different places and are relatively independent of each other's statuses.

    Note that I call it ArchivePartMeta, not ArchivePart, because unlike Archive, ArchivePartMeta has no field that
    points to actual data. Archive is called Archive instead of ArchiveMeta because Archive.archive_file actually points
    to the archive file.
    """

    archive: Archive = models.ForeignKey(to=Archive, on_delete=models.CASCADE)
    part_index = models.IntegerField(null=False)
    start_byte_index = models.IntegerField(null=False)
    end_byte_index = models.IntegerField(null=False)
    part_checksum = models.CharField(max_length=32, null=True)
    uploaded = models.BooleanField(null=False)
    cached = models.BooleanField(null=False)

    def __str__(self):
        return f"Archive {self.archive.archive_name}'s part {self.part_index}"

    def get_size(self):
        return self.end_byte_index - self.start_byte_index


class PersistentTransferJob(models.Model):
    """
    abstraction of file part upload/download between local server and S3
    If transfer_type is "Upload":
        -   archive.archive_file.name should point to the media/... path that is the file
        -   file_part_index ranges from 0 to n, where n+1 is the number of file chunks
        -   start_byte_index, end_byte_index will be passed into .seek() and .read() to extract the file part from the
            file

    """

    TRANSFER_TYPES = [("upload", "upload"), ("download", "download")]
    JOB_STATUSES = [("scheduled", "scheduled"), ("completed", "completed")]

    content_meta: ArchivePartMeta = models.ForeignKey(
        to=ArchivePartMeta, on_delete=models.CASCADE
    )
    transfer_type = models.CharField(max_length=10, null=False, choices=TRANSFER_TYPES)
    status = models.CharField(
        max_length=512, null=False, default="scheduled", choices=JOB_STATUSES
    )
    date_created = models.DateTimeField(default=timezone.now, null=False)
    date_started = models.DateTimeField(null=True)
    date_completed = models.DateTimeField(null=True)

    def __str__(self):
        transfer_type = self.transfer_type
        direction = "to" if transfer_type == "upload" else "from"
        username = self.content_meta.archive.owner.username
        archive_id = self.content_meta.archive.archive_id
        part_index = self.content_meta.part_index
        return f"{transfer_type} {direction} {username}/{archive_id}/{part_index}"
