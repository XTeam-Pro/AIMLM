#!/usr/bin/env bash

set -e
set -x

# Wait for Redis
echo "Checking connection to Redis..."
until redis-cli -u $REDIS_URL ping | grep -q "PONG"; do
  >&2 echo "Redis isn't available - waiting..."
  sleep 1
done
echo "Redis is ready!"

# Run migrations
echo "Running database migrations..."
alembic upgrade head
echo "Migrations applied successfully."

# Verify database is fully ready (tables exist)
echo "Verifying database schema..."
python app/backend_pre_start.py

# Create initial data
echo "Creating initial data..."
python app/initial_data.py
echo "Initial data created successfully."