#!/bin/bash

set -e

echo "Waiting for database..."
until python -c "
import sys
import psycopg2
import os

try:
    conn = psycopg2.connect(
        dbname=os.getenv('DATABASE_NAME', 'kiosk_db'),
        user=os.getenv('DATABASE_USER', 'kiosk_user'),
        password=os.getenv('DATABASE_PASSWORD', ''),
        host=os.getenv('DATABASE_HOST', 'db'),
        port=os.getenv('DATABASE_PORT', '5432')
    )
    conn.close()
    sys.exit(0)
except psycopg2.OperationalError:
    sys.exit(1)
" 2>/dev/null; do
  echo "Database is unavailable - sleeping"
  sleep 1
done

echo "Database is ready!"

echo "Running migrations..."
MIGRATE_OUTPUT=$(python manage.py migrate --noinput 2>&1)
echo "$MIGRATE_OUTPUT"

if echo "$MIGRATE_OUTPUT" | grep -q "have changes that are not yet reflected in a migration"; then
    echo ""
    echo "⚠️  Warning: Some models have changes that are not yet reflected in migrations."
    echo "   Run 'make makemigrations-dev' to create migrations, then restart the container."
    echo ""
fi

echo "Starting development server..."
exec "$@"

