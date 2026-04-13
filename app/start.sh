#!/usr/bin/env sh
set -e

if [ -z "$DB_HOST" ] || [ -z "$DB_PORT" ]; then
  echo "DB_HOST and DB_PORT must be set"
  exit 1
fi

until pg_isready -h "$DB_HOST" -p "$DB_PORT"; do
  echo "Waiting for database at $DB_HOST:$DB_PORT..."
  sleep 2
done

echo "Database is ready. Running migrations..."
alembic upgrade head

echo "Starting API..."
if [ "$ENV" = "dev" ]; then
  exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
  exec uvicorn app.main:app --host 0.0.0.0 --port 8000
fi
