import typing as ty

from archive.models import Archive


def run(logger=print):
    """
    Iterate through all instances of archive models, and for each of which, check if the corresponding complete file 
    exists in the media/archives directory and if the complete file's checksum matches the recorded checksum.
    -   exists and in good health:
        set "cached" to True
    -   exists but in bad health:
        Do nothing for now; we will address corrupted archive files later
    -   does not exist:
        Set 'cached' to False
    """
    logger(f"Inspecting local archive files")
    for archive in Archive.objects.all():
        logger(f"Inspecting local archive file for {str(archive)}")
        local_checksum = archive.get_local_checksum()
        if not local_checksum:
            logger(f"Local archive file for {str(archive)} does not exist")
            archive.cached = False
        else:
            if local_checksum == archive.archive_file_checksum:
                logger(f"Local archive file for {str(archive)} exists in good health")
                archive.cached = True
        archive.save()
