#!/usr/bin/env bash

# create virtual environment
python3 -m venv env
# activate virtual environment and install requirements
source env/bin/activate && pip install -r requirements.txt
# remove database and migrations
dropdb greeklinkdb
sudo rm -rf core/migrations
sudo rm -rf rush/migrations
sudo rm -rf organizations/migrations
sudo rm -rf cal/migrations
# migrations and static files
createdb greeklinkdb
python manage.py makemigrations core
python manage.py makemigrations organizations
python manage.py makemigrations rush
python manage.py makemigrations cal
python manage.py migrate_schemas
python manage.py collectstatic --noinput

# load fixtures
python manage.py loaddata auth.json
python manage.py loaddata settings.json
