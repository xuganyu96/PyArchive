# Archive status 
There are several two types of statuses for an archive: remote status and local status. Remote status describes the 
state of the archive file on AWS S3; local status describes the state of archive file on local server's disk. There are
the following possibilities of remote and local status combinations:
1. When an archive is first created, the archive file is uploaded to the local server's disk. In this case, set 
`local_status` to `cached`, and `remote_status` to `scheduled_for_upload`.
2. When there is at least one file part for this archive that has been uploaded, but not all file parts have been 
uploaded, `remote_status` is `uploading`, and `local_status` is `cached`.
3. When all file parts of this archive have been uploaded