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
    archive_id = models.CharField(max_length=64, default=uuid.uuid4, primary_key=True)
    archive_file = models.FileField(upload_to=archive_file_save_path)
    archive_name = models.CharField(max_length=512, null=True)
    owner: User = models.ForeignKey(to=User, on_delete=models.CASCADE)
    date_created = models.DateTimeField(default=timezone.now)

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


class PersistentFileTransfer(models.Model):
    """
    abstraction of file part upload/download between local server and S3
    If transfer_type is "Upload":
        -   archive.archive_file.name should point to the media/... path that is the file
        -   file_part_index ranges from 0 to n, where n+1 is the number of file chunks
        -   start_byte_index, end_byte_index will be passed into .seek() and .read() to extract the file part from the
            file

    """
    batch_id = models.CharField(max_length=64, default=uuid.uuid4, primary_key=True)
    archive: Archive = models.ForeignKey(to=Archive, on_delete=models.CASCADE)
    file_part_index = models.IntegerField(null=False)
    start_byte_index = models.IntegerField(null=False)
    end_byte_index = models.IntegerField(null=False)
    transfer_type = models.CharField(max_length=512, null=False)
    status = models.CharField(max_length=512, null=False, default='scheduled')
    date_created = models.DateTimeField(default=timezone.now, null=False)
    date_started = models.DateTimeField(null=True)
    date_completed = models.DateTimeField(null=True)

    class Meta:
        unique_together = (('batch_id', 'archive', 'file_part_index'),)

    def __str__(self):
        return self.archive.archive_id + ':' + self.batch_id + ':' + str(self.file_part_index)

