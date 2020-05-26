from archive.models import ArchivePartMeta
from .s3portal.portal_utils import get_active_conn, has_remote, remove_remote, has_healthy_remote, has_local_file, \
    queue_upload


HEARTBEAT = 10


def run(logger=print):
    """
    If there is no active connection, then sleep for 10 seconds.
    If there is an active connection, then iterate through all archive part instances:
    -   if the corresponding remote file exists in good health, then set "uploaded" to True
    -   if not, check the following:
        -   if remote file exists, then delete it
        -   set "uploaded" to False
        -   if local_file exists, the queue an upload job
    """
    active_conn = get_active_conn()
    if not active_conn:
        logger(f"No active connection found")
    logger("Checking remote health for all archive parts")
    for archive_part_meta in ArchivePartMeta.objects.all():
        archive_part_meta: ArchivePartMeta = archive_part_meta
        logger(f"Checking remote health for archive part {archive_part_meta}")
        if has_healthy_remote(archive_part_meta, active_conn):
            logger(f"{archive_part_meta} has healthy remote")
            archive_part_meta.uploaded = True
        else:
            if has_remote(archive_part_meta, active_conn):
                logger(f"{archive_part_meta}'s remote fails checksum matching and will be deleted")
                remove_remote(archive_part_meta, active_conn)
            archive_part_meta.uploaded = False
            if has_local_file(archive_part_meta):
                logger(f"Queuing {archive_part_meta}")
                queue_upload(archive_part_meta)
        archive_part_meta.save()

    #   After making sure that each archive_part's uploaded flag is correct, remove all remote files that have no
    #   corresponding "uploaded" archive_part
    logger("Cleaning up orphaned remote files")
    uploaded_archive_parts = ArchivePartMeta.objects.filter(uploaded=True)
    uploaded_archive_part_keys = [part.get_remote_key() for part in uploaded_archive_parts]
    s3 = active_conn.get_resource('s3')
    active_bucket = s3.Bucket(active_conn.connection_id)
    for obj in active_bucket.objects.all():
        if obj.key not in uploaded_archive_part_keys:
            #   This object is not supposed to have a remote
            logger(f"Deleting {obj} for not having corresponding record in database")
            obj.delete()

