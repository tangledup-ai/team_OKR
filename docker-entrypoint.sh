#!/bin/sh

set -e

# Wait for postgres
if [ -n "$DB_HOST" ]; then
    echo "Waiting for postgres at $DB_HOST:$DB_PORT..."
    while ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2> /dev/null; do
        echo "Waiting for postgres..."
        sleep 1
    done
    echo "PostgreSQL started"
fi

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Execute the command passed to docker
exec "$@"
