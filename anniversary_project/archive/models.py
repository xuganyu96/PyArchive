import uuid
from os.path import basename

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse


def archive_file_save_path(instance, filename) -> str:
    """
    :param instance: an Archive instance
    :param filename: the name of the file when it was uploaded
    :return: the path to which the file will be saved (under MEDIA_ROOT directory)
    """
    return f"archives/{instance.owner.username}/{instance.archive_id}/{filename}"


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
        return self.archive_id + ' owned by ' + self.owner.username

    #   Define the method for returning the URL of specific archive's detail page
    def get_absolute_url(self):
        return reverse('archive-detail', kwargs={'pk': self.archive_id})

    def delete(self, using=None, keep_parents=False):
        """
        Overwrite the default delete method so the file would be deleted when the model instance is deleted
        """
        self.archive_file.storage.delete(self.archive_file.name)
        super().delete()


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
    TRANSFER_TYPES = [('upload', 'upload'), ('download', 'download')]
    JOB_STATUSES = [('scheduled', 'scheduled'), ('completed', 'completed')]

    content_meta: ArchivePartMeta = models.ForeignKey(to=ArchivePartMeta, on_delete=models.CASCADE)
    transfer_type = models.CharField(max_length=10, null=False, choices=TRANSFER_TYPES)
    status = models.CharField(max_length=512, null=False, default='scheduled', choices=JOB_STATUSES)
    date_created = models.DateTimeField(default=timezone.now, null=False)
    date_started = models.DateTimeField(null=True)
    date_completed = models.DateTimeField(null=True)

    def __str__(self):
        transfer_type = self.transfer_type
        direction = 'to' if transfer_type == 'upload' else 'from'
        username = self.content_meta.archive.owner.username
        archive_id = self.content_meta.archive.archive_id
        part_index = self.content_meta.part_index
        return f"{transfer_type} {direction} {username}/{archive_id}/{part_index}"

