#! /usr/bin/env bash

set -e
set -x

# Let the DB start
python app/backend_pre_start.py

# Let the MongoDB be initialized
python app/core/mongo_db.py
# Run migrations
alembic upgrade head

# Create initial data in DB
python app/initial_data.py
