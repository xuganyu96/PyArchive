import os
import hashlib

from django.forms import ModelForm

from .models import Archive, ArchivePartMeta, PersistentTransferJob, get_file_checksum
from anniversary_project.settings import MEDIA_ROOT


class ArchiveForm(ModelForm):
    class Meta:
        model = Archive
        fields = ["archive_file", "archive_name"]

    def save(self, *args, **kwargs):
        """
        Overwrite the parent class saving method to do file checksum
        """
        super().save(*args, **kwargs)
        archive_file_path = os.path.join(MEDIA_ROOT, self.instance.archive_file.name)
        checksum = get_file_checksum(archive_file_path)
        self.instance.archive_file_checksum = checksum
        self.instance.save()
        self.initialize_archive_parts(archive=self.instance)

    @classmethod
    def initialize_archive_parts(
        cls, archive: Archive, chunk_size: int = 5 * (2 ** 20)
    ):
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
            part_checksum = cls.get_file_part_checksum(
                archive, start_byte_index, end_byte_index
            )
            archive_part = ArchivePartMeta(
                archive=archive,
                part_index=archive_part_index,
                start_byte_index=start_byte_index,
                end_byte_index=end_byte_index,
                part_checksum=part_checksum,
                uploaded=False,
                cached=False,
            )
            archive_part.save()
            upload_job = PersistentTransferJob(
                content_meta=archive_part, transfer_type="upload", status="scheduled"
            )
            upload_job.save()

            start_byte_index += chunk_size
            archive_part_index += 1

    @classmethod
    def get_file_part_checksum(
        cls,
        archive: Archive,
        start_byte_index: int,
        end_byte_index: int,
        hash_func=hashlib.md5,
    ) -> str:
        """
        :param archive:
        :param start_byte_index:
        :param end_byte_index:
        :param hash_func:
        :return: the checksum of the file part using the hashing function. I trust that an archive part will be
        small so I will not implement batch processing.
        """
        full_path = os.path.join(MEDIA_ROOT, archive.archive_file.name)
        with open(full_path, "rb") as f:
            file_hash = hash_func()
            f.seek(start_byte_index)
            part_size = end_byte_index - start_byte_index
            file_hash.update(f.read(part_size))

        return file_hash.hexdigest()
