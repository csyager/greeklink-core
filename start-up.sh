#!/usr/bin/env bash

# create virtual environment
python3 -m venv env
# activate virtual environment and install requirements
source env/bin/activate && pip install -r requirements.txt
# remove database and migrations
sudo rm db.sqlite3
sudo rm -rf core/migrations
# migrations and static files
python manage.py makemigrations core
python manage.py makemigrations rush
python manage.py migrate
python manage.py collectstatic --noinput

# load fixtures
python manage.py loaddata db.json