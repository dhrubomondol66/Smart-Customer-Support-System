#!/usr/bin/env bash
# build.sh — Render build script
# Runs once on every deploy before the start command.
set -o errexit   # exit on error

pip install --upgrade pip
pip install -r requirements.txt

# Collect static files (WhiteNoise serves them)
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate --no-input
