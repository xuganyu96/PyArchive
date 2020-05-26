import os
import shutil
import logging

from archive.models import Archive, ArchivePartMeta
from archive.forms import ArchiveForm
from anniversary_project.settings import MEDIA_ROOT


CACHE_DIR = os.path.join(MEDIA_ROOT, "cache")


def check_cache_health(archive_id: str) -> bool:
    """
    :param archive_id:
    :return: True if and only if the all parts are present and are in good health
    """
    archive = Archive.objects.get(pk=archive_id)
    print(f"Checking cache health for archive {archive}'s parts")
    archive_parts_meta = ArchivePartMeta.objects.filter(archive=archive)
    archive_cache_dir = os.path.join(
        CACHE_DIR, str(archive.owner.username), str(archive.archive_id)
    )
    ready_for_assembly = True
    for archive_part_meta in archive_parts_meta:
        print(f"Inspecting cache file for {archive_part_meta}")
        cache_part_file_path = os.path.join(
            archive_cache_dir, str(archive_part_meta.part_index)
        )
        if not (os.path.exists(cache_part_file_path) and os.path.isfile(cache_part_file_path)):
            #   If the desired path doesn't point to an existing file, then the archive is not ready for assembly
            print(f"File cache for {archive_part_meta} does not exist")
            ready_for_assembly = False
        else:
            cache_part_file_checksum = ArchiveForm.get_file_checksum(
                file_path=cache_part_file_path
            )
            if cache_part_file_checksum != archive_part_meta.part_checksum:
                #   If the file part's checksum does not check out, then remove the file part
                print(f"Archive file part at {cache_part_file_path} fails checksum matching")
                os.remove(cache_part_file_path)
                archive_part_meta.cached = False
            else:
                print(f"Archive file part at {cache_part_file_path} is in good health")
                archive_part_meta.cached = True
            archive_part_meta.save()

    return ready_for_assembly


def assemble_archive(archive_id: str):
    """
    :param username:
    :param archive_id:
    :return: read in the parts in cache directory and write all bytes in a single swoop to the archive directory
    """
    archive = Archive.objects.get(archive_id=archive_id)
    username = archive.owner.username
    cache_dir = os.path.join(MEDIA_ROOT, "cache", username, archive_id)
    archive_dir = os.path.join(MEDIA_ROOT, "archives", username, archive_id)
    #   Delete archive_dir and remake it
    shutil.rmtree(path=archive_dir)
    os.makedirs(archive_dir)
    #   Sort the file parts numerically by the index
    file_part_names = os.listdir(cache_dir)
    file_part_names.sort(key=lambda x: int(x))
    #   Find the original file name
    archive: Archive = Archive.objects.get(pk=archive_id)
    archive_file_name = os.path.basename(archive.archive_file.name)
    archive_file_path = os.path.join(archive_dir, archive_file_name)
    #   Start writing in batches:
    with open(archive_file_path, "ab") as f:
        for file_part_name in file_part_names:
            file_part_path = os.path.join(cache_dir, file_part_name)
            with open(file_part_path, "rb") as p:
                print(f"Appending {file_part_path} to {archive_file_path}")
                f.write(p.read())
    #   Confirm the checksum
    print(f"Verifying assembled file at {archive_file_path}")
    written_checksum = ArchiveForm.get_file_checksum(file_path=archive_file_path)
    if written_checksum == archive.archive_file_checksum:
        print(f"Successfully assembled archive at {archive_file_path}")
        archive.cached = True
        archive.save()
        #   Before deleting the directory holding archive part files, set the model instance's cached to False
        for archive_part in ArchivePartMeta.objects.filter(archive=archive):
            archive_part.cached = False
            archive_part.save()
        shutil.rmtree(cache_dir)
    else:
        print(f"Oh-oh something went wrong")


def run(logger=print):
    """
    Check integrity of local cache and assemble them into complete archive if all of them are in good health
    """
    if not (os.path.exists(CACHE_DIR) and os.path.isdir(CACHE_DIR)):
        logger(f"media/cache directory does not exist; skipping inspection")
    else:
        logger(f"Checking all archive parts' health")
        for archive in Archive.objects.all():
            logger(f"Checking archive {archive}'s local partition cache")
            ready_for_assembly = check_cache_health(archive.archive_id)
            if ready_for_assembly:
                logger(f"Archive {archive} is ready for assembly")
                assemble_archive(archive.archive_id)
            else:
                logger(f"Archive {archive} is not ready for assembly")
