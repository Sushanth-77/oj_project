#!/usr/bin/env bash
# startup.sh - Runs when container starts

echo "🚀 Container starting up..."

# Set environment
export PYTHONPATH="/app/oj_project:$PYTHONPATH"
export DJANGO_SETTINGS_MODULE=oj_project.settings

cd /app/oj_project

# Wait for database to be ready
echo "⏳ Waiting for database..."
python -c "
import time
import django
import os
django.setup()

from django.db import connection
from django.core.management.color import no_style

max_retries = 30
for i in range(max_retries):
    try:
        connection.ensure_connection()
        print(f'✅ Database connected on attempt {i+1}')
        break
    except Exception as e:
        print(f'⏳ Database not ready (attempt {i+1}/{max_retries}): {e}')
        if i == max_retries - 1:
            print('❌ Database connection failed after all retries')
            exit(1)
        time.sleep(2)
"

# Apply migrations to the actual database
echo "🔄 Applying migrations to production database..."
python manage.py migrate --verbosity=2

# Create superuser if it doesn't exist
echo "👤 Setting up admin user..."
python -c "
import django
django.setup()
from django.contrib.auth.models import User
import os

try:
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        print('✅ Admin user created: admin/admin123')
    else:
        print('✅ Admin user already exists')
except Exception as e:
    print(f'⚠️ Could not create admin user: {e}')
"

echo "✅ Startup completed, starting gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 --workers 4 oj_project.wsgi:application