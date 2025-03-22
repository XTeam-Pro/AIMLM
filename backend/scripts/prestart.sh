#! /usr/bin/env bash

set -e
set -x

# Run migrations
echo "Running database migrations..."
alembic upgrade head
echo "Migrations applied successfully."


# Let the DB start
python app/backend_pre_start.py


# Create initial data in DB
python app/initial_data.py
