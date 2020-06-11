#!/bin/bash
apt-get update
apt-get install -y awscli
aws s3 sync s3://bruce-ssh-public-keys /tmp/temporary_keys
cd /tmp/temporary_keys


for username in *
do   
  adduser --disabled-password --gecos "" $username
  echo "$username:password" | chpasswd
  usermod -aG sudo $username
  mkdir /home/$username/.ssh
  cat /tmp/temporary_keys/$username/*.pub >> /home/$username/.ssh/authorized_keys
done
