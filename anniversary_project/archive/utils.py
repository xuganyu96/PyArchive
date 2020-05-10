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


def can_uncache(archive) -> bool:
    """
    :param archive:
    :return: return True if and only if all instances of ArchivePartMeta of this archive is uploaded
    """
    archive_parts = ArchivePartMeta.objects.filter(archive=archive)
    for archive_part_meta in archive_parts:
        if not archive_part_meta.uploaded:
            return False
    return True


def uncache(archive):
    """
    :param archive:
    :return: None; delete the file in MEDIA_ROOT/archive/username/archive_id/ but do not delete the directory
    """
    archive.archive_file.storage.delete(archive.archive_file.name)
    archive.cached = False
    archive.save()
