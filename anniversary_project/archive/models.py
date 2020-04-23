import uuid

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Archive(models.Model):
    archive_id = models.CharField(max_length=64, default=str(uuid.uuid4()), primary_key=True)
    file_full_name = models.CharField(max_length=512, null=False)
    archive_name = models.CharField(max_length=512, null=True)
    owner_id = models.ForeignKey(to=User, on_delete=models.CASCADE)
    date_created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.archive_id

