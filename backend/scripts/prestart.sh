#!/usr/bin/env bash

set -e
set -x


echo "Running database migrations..."
alembic upgrade head
echo "Migrations applied successfully."

python app/backend_pre_start.py

# Create initial data
python app/initial_data.py