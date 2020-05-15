#!/bin/sh

migration_files=`ls */*/migrations/*.py | grep -v -e '__init__'`
for migration_file in $migration_files
do
  echo $migration_file
  rm $migration_file
done

rm ./anniversary_project/db.sqlite3
rm -r ./anniversary_project/media/archives/*
rm -r ./anniversary_project/media/cache/*
rm -r ./anniversary_project/media/profile_pics/*

cd anniversary_project
python manage.py makemigrations
python manage.py migrate
export DJANGO_SUPERUSER_PASSWORD=admin
python manage.py createsuperuser --no-input --email "xuganyu96@gmail.com" --username admin
