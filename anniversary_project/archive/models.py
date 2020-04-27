import uuid

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Archive(models.Model):
    archive_id = models.CharField(max_length=64, default=str(uuid.uuid4()), primary_key=True)
    file_full_name = models.CharField(max_length=512, null=False)
    archive_name = models.CharField(max_length=512, null=True)
    owner: User = models.ForeignKey(to=User, on_delete=models.CASCADE)
    date_created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.archive_id + 'owned by ' + self.owner.username


class PersistentFileTransfer(models.Model):
    batch_id = models.CharField(max_length=64, default=str(uuid.uuid4()), primary_key=True)
    archive: Archive = models.ForeignKey(to=Archive, on_delete=models.DO_NOTHING)
    file_part_index = models.IntegerField(null=False)
    transfer_type = models.CharField(max_length=512, null=False)
    status = models.CharField(max_length=512, null=False)
    date_created = models.DateTimeField(default=timezone.now, null=False)
    date_started = models.DateTimeField(null=True)
    date_completed = models.DateTimeField(null=True)

    class Meta:
        unique_together = (('batch_id', 'archive', 'file_part_index'),)

    def __str__(self):
        return self.archive.archive_id + ':' + self.batch_id + ':' + str(self.file_part_index)

