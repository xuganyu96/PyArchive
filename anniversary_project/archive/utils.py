import os

from .models import Archive, ArchivePartMeta, PersistentTransferJob
from anniversary_project.settings import MEDIA_ROOT


def initialize_archive(archive: Archive, chunk_size: int = 5*(2**20)):
    """
    :param archive: an Archive model instance that was just created through the web UI
    :param chunk_size: the maximal number of bytes for each archive's part, default if 5MB
    :return: Create the ArchivePart instances and the schedule the PersistentTransferJob into the database
    """
    archive_file_path = os.path.join(MEDIA_ROOT, archive.archive_file.name)
    archive_file_size = os.path.getsize(archive_file_path)

    start_byte_index = 0
    archive_part_index = 0
    while start_byte_index < archive_file_size:
        end_byte_index = min(archive_file_size, start_byte_index + chunk_size)
        archive_part = ArchivePartMeta(archive=archive,
                                       part_index=archive_part_index,
                                       start_byte_index=start_byte_index,
                                       end_byte_index=end_byte_index,
                                       uploaded=False,
                                       cached=False)
        archive_part.save()
        upload_job = PersistentTransferJob(content_meta=archive_part,
                                           transfer_type='upload',
                                           status='scheduled')
        upload_job.save()

        start_byte_index += chunk_size
        archive_part_index += 1
