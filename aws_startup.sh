#!/usr/bin/env bash

sudo rm db.sqlite3
sudo rm -rf core/migrations
# migrations and static files
python manage.py makemigrations core
python manage.py migrate
python manage.py collectstatic --noinput

# load fixtures
python manage.py loaddata db.json