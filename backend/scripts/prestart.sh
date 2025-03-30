#!/usr/bin/env bash

set -e
set -x
echo "Checking connection to Redis..."
until redis-cli -u $REDIS_URL ping | grep -q "PONG"; do
  >&2 echo "Redis isn't available - waiting..."
  sleep 1
done

echo "Redis is ready!"

echo "Running database migrations..."
alembic upgrade head
echo "Migrations applied successfully."

python app/backend_pre_start.py

# Create initial data
python app/initial_data.py