import time
import typing as ty
import os

from botocore.errorfactory import ClientError

from archive.models import Archive, ArchivePartMeta, PersistentTransferJob
from s3connections.models import S3Connection
from .s3portal.portal_utils import get_active_conn, has_remote, remove_remote, has_healthy_remote, has_local_file, \
    queue_upload


HEARTBEAT = 10


def run():
    """
    If there is no active connection, then sleep for 10 seconds.
    If there is an active connection, then iterate through all archive part instances:
    """
    active_conn = get_active_conn()
    if not active_conn:
        print(f"No active connection found")
    for archive_part_meta in ArchivePartMeta.objects.all():
        archive_part_meta: ArchivePartMeta = archive_part_meta
        if has_healthy_remote(archive_part_meta, active_conn):
            print(f"{archive_part_meta} has healthy remote")
            archive_part_meta.uploaded = True
        else:
            if has_remote(archive_part_meta, active_conn):
                print(f"{archive_part_meta}'s remote fails checksum matching and will be deleted")
                remove_remote(archive_part_meta, active_conn)
            archive_part_meta.uploaded = False
            if has_local_file(archive_part_meta):
                print(f"Queuing {archive_part_meta}")
                queue_upload(archive_part_meta)
        archive_part_meta.save()
