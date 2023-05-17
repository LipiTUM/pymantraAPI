#!/usr/bin/env sh

python manage.py makemigrations
python manage.py migrate auth
python manage.py migrate

echo "Waiting for sql-db..."
while ! nc -z sql-db 3306; do
	sleep 0.1
done
echo "Found sql-db. Establishing connection..."
python manage.py generate_admin

# Wait for the neo4j database
echo "Waiting for neo4j-db..."
while ! nc -z neo4j-db 7687; do
	sleep 0.1
done
echo "Found neo4j-db. Establishing connection..."
while ! python scripts/test_neo4j_db_connection.py; do
	sleep 1
done
echo "Connection to neo4j-db established."

python manage.py initialize_neo4j_db

echo "Running gunicorn with $N_WORKERS workers"

gunicorn pymantra_api.wsgi:application --bind 0.0.0.0:80 --timeout 480 \
             --workers "$N_WORKERS"
