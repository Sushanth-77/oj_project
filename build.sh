#!/usr/bin/env bash
# exit on error
set -o errexit

# Make sure we have proper permissions (Linux/Unix)
chmod +x "$0" 2>/dev/null || true

# Install dependencies
pip install -r requirements.txt

# Change to the Django project directory
cd oj_project

# Create migrations (in case any are missing)
python manage.py makemigrations

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --no-input