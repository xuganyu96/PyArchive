# PyArchive
In celebration of my anniversary at my first full-time job out of college, I would like to apply what I have learned from
my work, and demonstrate my understanding of software development through a web application.

## Introduction
This web application (subsequently referred to as `pyarchive`) is intended as a file backup management software. It will
have a web UI that the user can interface with, and a daemon that runs the background and performs local file system's
maintenance and data transfers between remote (an AWS S3 in this instance) and local file system.

The basic workflow goes as follows:
1. User can register account, log in, and create an archive by uploading a file and specifying an archive name
2. User can view all the archives that he/she has created, including their statuses locally and remotely:
    1. An archive can be locally present (called "cached") or not.
    2. An archive's remote present takes the form of indexed file parts. An archive's file is broken into parts when 
    uploading to remote because this way, the server can experience an intermittent outage without losing too much 
    progress
3. User can directly download an archive if it is locally present; if an archive is not locally present, then the user 
can request that it be cached from remote.
4. User can delete an archive, which will remove it from local and remote storage.

## Baseline: April 30, 2020
As of the last day of April of 2020, I have watched a number of tutorials of Django 3 (my choice of web framework) and 
implemented the following features that will server as a baseline (a stable build of some sort):
1. An user authentication system where a user can register an account with username, password, an optional email field. 
The registration process will require the user to confirm the password by typing it twice, and post an error message 
(in red) that will disappear after an refresh. 
2. here is a default profile picture stored under `/media/default.png`, and the user can upload custom profile picture, 
which will be stored in the `/media/profile_pics` directory. All of the profile pics can be accessed through URL, as 
well. 
3. The user needs to log in before being able to access the `/archive` urls and `s3` urls. If the user attempts to 
access `/archive` or `/s3` without logging in, he will be redirected back to the login page.
4. There is a complete CUD (Create, Update, Delete) paradigm for Archive instances, and S3 Connection instances:
    1. Archive instances:
        1. At creation, the user can upload a file and specify an archive name. The archive file will be stored under 
        `/media/archives/<username>/<archive_id>/file`
        2. At detail page, the user can view a number of attributes: archive id, archive name, file checksum, file parts
        and their remote/local statuses, file parts' checksum
        3. At deletion, the file, and the `<archive_id>` directory will both be deleted
    2. S3 Connection
        1. At creation, the user specify connection name, AWS access key, AWS secret key, and region
        2. After creation, the user can validate the S3 connection and make the current S3 connection the active 
        connection in the detail page.
        3. Only staff members can make changes to S3 Connections. If an under-privileged user tries to modify an S3
        Connection instance, an error message will show up.
        