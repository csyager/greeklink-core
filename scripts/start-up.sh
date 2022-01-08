#!/usr/bin/env bash

# create virtual environment
python3 -m venv env
# activate virtual environment and install requirements
source env/bin/activate && pip install -r requirements.txt

# remove migrations
sudo rm -rf core/migrations
sudo rm -rf rush/migrations
sudo rm -rf organizations/migrations
sudo rm -rf cal/migrations

# delete everything from media
sudo rm -rf media/

# stop database container if running
docker stop greekrho-postgres || true

# wait for database container to be stopped
while docker ps -f name=greekrho-postgres | grep greekrho-postgres; do
	sleep 0.1;
done;

# configure docker postgres db
# username: greeklinkuser
# password: greeklinkdb
# host: localhost (127.0.0.1)
# port: 5432
docker run \
	-d \
	-P \
	--env POSTGRES_HOST_AUTH_METHOD=trust \
	--env POSTGRES_USER=greeklinkuser \
	--env POSTGRES_DB=greeklinkdb \
	-p 5432:5432 \
	--rm \
	--name greekrho-postgres \
	postgres:latest 

# wait until database container is ready to accept connections
until pg_isready -h localhost -p 5432 -U greeklinkuser -d greeklinkdb; do
	sleep 1.0;
done;

# migrations and static files
python manage.py makemigrations core
python manage.py makemigrations organizations
python manage.py makemigrations rush
python manage.py makemigrations cal
python manage.py migrate_schemas
python manage.py collectstatic --noinput

# load fixtures
echo "from organizations.models import Client; Client.objects.create(domain_url='test.localhost', schema_name='test', name='Test Tenant'); Client.objects.create(domain_url='localhost', schema_name='public', name='public'); exit();" | python manage.py shell
python manage.py tenant_command loaddata --schema=test auth.json
python manage.py tenant_command loaddata --schema=test settings.json 

echo "Done!"
