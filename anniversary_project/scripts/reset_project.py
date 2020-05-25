from admintools.models import AdminTool
from .s3portal.portal_utils import reset_s3_connection


def initialize_admin_tools():
    """
    Create a few admin tools
    """
    assemble_archive = AdminTool(
        tool_id='assemble_archive',
        tool_title='Assemble Archive From Parts',
        tool_description='Check the health of local archive parts, and assemble them if parts are present',
        deployed=True
    )
    assemble_archive.save()

    execute_data_transfer = AdminTool(
        tool_id='execute_data_transfer',
        tool_title='Execute data transfer',
        tool_description='Check if there are data transfer jobs to be executed and execute them',
        deployed=True
    )
    execute_data_transfer.save()

    sync_archive_to_db = AdminTool(
        tool_id='sync_archive_to_db',
        tool_title='Sync local archive to database',
        tool_description='Check the existence and health of local archive files, and update database accordingly',
        deployed=True
    )
    sync_archive_to_db.save()

    sync_remote_db = AdminTool(
        tool_id='sync_remote_db',
        tool_title='Sync S3 buckets to database',
        tool_description='Check the existence and health of remote archive parts, and update database accordingly',
        deployed=True
    )
    sync_remote_db.save()


def run():
    reset_s3_connection()
    initialize_admin_tools()
