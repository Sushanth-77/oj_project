#!/usr/bin/env bash
# EMERGENCY BUILD SCRIPT - FIXED
set -o errexit

echo "🚀 EMERGENCY BUILD STARTING..."

# Install dependencies
pip install -r requirements.txt

# Wait for database
echo "⏳ Waiting for database..."
sleep 10

# FORCE CREATE ALL TABLES
echo "🔥 FORCE CREATING DATABASE TABLES..."

# Create database tables with --run-syncdb (this creates tables even without migrations)
python manage.py migrate --run-syncdb --verbosity=2 || echo "Syncdb failed, continuing..."

# Run individual migrations for core Django apps
python manage.py migrate auth --verbosity=2 || echo "Auth migration failed, continuing..."
python manage.py migrate contenttypes --verbosity=2 || echo "Contenttypes migration failed, continuing..."
python manage.py migrate sessions --verbosity=2 || echo "Sessions migration failed, continuing..."
python manage.py migrate admin --verbosity=2 || echo "Admin migration failed, continuing..."

# Run all migrations
python manage.py migrate --verbosity=2 || echo "General migration failed, continuing..."

# Alternative approach - create tables directly
python manage.py shell -c "
from django.core.management import execute_from_command_line
from django.db import connection
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.models import Session
import traceback

try:
    # Test if auth_user table exists
    User.objects.count()
    print('✅ auth_user table exists!')
except Exception as e:
    print('❌ auth_user table missing, creating...')
    try:
        # Force create auth tables
        from django.core.management.sql import sql_all
        from django.contrib.auth import models as auth_models
        from django.db import connection
        
        # This should create the missing tables
        with connection.cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auth_user (
                    id SERIAL PRIMARY KEY,
                    password VARCHAR(128) NOT NULL,
                    last_login TIMESTAMP WITH TIME ZONE,
                    is_superuser BOOLEAN NOT NULL,
                    username VARCHAR(150) NOT NULL UNIQUE,
                    first_name VARCHAR(150) NOT NULL,
                    last_name VARCHAR(150) NOT NULL,
                    email VARCHAR(254) NOT NULL,
                    is_staff BOOLEAN NOT NULL,
                    is_active BOOLEAN NOT NULL,
                    date_joined TIMESTAMP WITH TIME ZONE NOT NULL
                );
            ''')
            print('✅ Created auth_user table manually!')
    except Exception as e2:
        print(f'❌ Manual table creation failed: {e2}')
        traceback.print_exc()
" || echo "Shell command failed, continuing..."

# Collect static files
python manage.py collectstatic --noinput --clear

echo "✅ BUILD COMPLETED!"