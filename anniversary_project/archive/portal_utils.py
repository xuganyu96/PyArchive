import os

from .models import PersistentFileTransfer, Archive
from anniversary_project.settings import MEDIA_ROOT


def schedule_archive_upload(archive: Archive, chunk_size: int = 5*(2**20)):
    """
    :param archive: an Archive model instance that was just created
    :param chunk_size: The size of file parts in bytes, default is 5MB
    :return: Create a number of upload jobs and save them into PersistentFileTransfer
    """
    archive_file_path = os.path.join(MEDIA_ROOT, archive.archive_file.name)
    archive_file_size = os.path.getsize(archive_file_path)

    #   start_byte_index and end_byte_index follow 0-based indexing, which means the last end_byte_index will be
    #   archive_file_size
    start_byte_index = 0
    while start_byte_index < archive_file_size:
        file_part_index = start_byte_index // chunk_size
        end_byte_index = min(archive_file_size, start_byte_index + chunk_size)
        upload_job = PersistentFileTransfer(archive=archive,
                                            file_part_index=file_part_index,
                                            start_byte_index=start_byte_index,
                                            end_byte_index=end_byte_index,
                                            transfer_type='upload',
                                            status='scheduled')
        upload_job.save()
        start_byte_index += chunk_size
