import os

from .models import Archive, ArchivePartMeta, PersistentTransferJob
from anniversary_project.settings import MEDIA_ROOT


def queue_archive_caching(archive: Archive):
    """
    :param archive: an archive object
    :return: None. However, create download job for each of the ArchiveMetaPart instance of archive instance and save
    them
    """
    archive_parts = ArchivePartMeta.objects.filter(archive=archive)
    for archive_part in archive_parts:
        download_job = PersistentTransferJob(
            content_meta=archive_part,
            transfer_type='download'
        )
        download_job.save()
