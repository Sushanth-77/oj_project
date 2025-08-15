#!/usr/bin/env bash
set -o errexit

echo "🚀 Starting deployment build..."

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install --no-cache-dir -r requirements.txt

# Set environment
echo "🔧 Setting up environment..."
export PYTHONPATH="/app/oj_project:$PYTHONPATH"
export DJANGO_SETTINGS_MODULE=oj_project.settings

# Change to Django directory
cd /app/oj_project

# Test database connection
echo "🔍 Testing database connection..."
python -c "
import django
django.setup()
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    print('Using SQLite fallback...')
"

# Show current migration status
echo "📊 Checking migration status..."
python manage.py showmigrations --verbosity=2 || echo "⚠️ Could not show migrations"

# Create migrations for all apps
echo "📝 Creating migrations..."
python manage.py makemigrations --verbosity=2

# Apply migrations with more verbose output
echo "🗄️ Applying migrations..."
python manage.py migrate --verbosity=2

# Verify auth_user table exists
echo "✅ Verifying database setup..."
python -c "
import django
django.setup()
from django.contrib.auth.models import User
from django.db import connection

try:
    # Test if we can query the User table
    count = User.objects.count()
    print(f'✅ auth_user table exists with {count} users')
    
    # List all tables
    with connection.cursor() as cursor:
        cursor.execute(\"\"\"
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        \"\"\")
        tables = cursor.fetchall()
        print(f'📊 Database tables: {[t[0] for t in tables]}')
        
except Exception as e:
    print(f'❌ Database verification failed: {e}')
    exit(1)
"

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput --verbosity=2

# Create superuser if needed (non-interactive)
echo "👤 Setting up admin user..."
python -c "
import django
django.setup()
from django.contrib.auth.models import User
import os

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password=os.environ.get('ADMIN_PASSWORD', 'admin123')
    )
    print('✅ Admin user created: admin/admin123')
else:
    print('✅ Admin user already exists')
"

echo "✅ Build completed successfully!"
echo "🎉 Ready to serve requests!"