import os
import hashlib

from django.forms import ModelForm

from .models import Archive, ArchivePartMeta, PersistentTransferJob
from anniversary_project.settings import MEDIA_ROOT


class ArchiveForm(ModelForm):
    class Meta:
        model = Archive
        fields = ['archive_file', 'archive_name']

    def save(self, *args, **kwargs):
        """
        Overwrite the parent class saving method to do file checksum
        """
        super().save(*args, **kwargs)
        archive_file_path = os.path.join(MEDIA_ROOT, self.instance.archive_file.name)
        checksum = self.get_file_checksum(archive_file_path)
        self.instance.archive_file_checksum = checksum
        self.instance.save()
        self.initialize_archive(archive=self.instance)

    @classmethod
    def get_file_checksum(cls, file_path, hash_func=hashlib.md5, chunk_size=8192) -> str:
        """
        :param file_path:
        :param hash_func:
        :param chunk_size:
        :return:
        """
        with open(file_path, 'rb') as f:
            file_hash = hash_func()
            remains = f.read(chunk_size)
            while remains:
                file_hash.update(remains)
                remains = f.read(chunk_size)

        return file_hash.hexdigest()

    @classmethod
    def initialize_archive(cls, archive: Archive, chunk_size: int = 5 * (2 ** 20)):
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

