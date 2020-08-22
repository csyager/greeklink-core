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

# delete everything from media
sudo rm -rf media/

# migrations and static files
createdb greeklinkdb
psql -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE greeklinkdb TO greeklinkuser;"
python manage.py makemigrations core
python manage.py makemigrations organizations
python manage.py makemigrations rush
python manage.py makemigrations cal
python manage.py migrate_schemas
python manage.py collectstatic --noinput

# load fixtures
echo "from organizations.models import Client; Client.objects.create(domain_url='test.localhost', schema_name='test', name='Test Tenant', community='test_community', paid_until='2100-12-31'); exit();" | python manage.py shell
python manage.py tenant_command loaddata --schema=test auth.json
python manage.py tenant_command loaddata --schema=test settings.json 
