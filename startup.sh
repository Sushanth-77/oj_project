#!/usr/bin/env bash
set -o errexit

echo "🚀 Starting deployment..."

cd oj_project

# Apply database migrations
echo "🔄 Applying migrations..."
python manage.py migrate --noinput

# Create admin user
echo "👤 Creating admin user..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oj_project.settings')
django.setup()

try:
    from django.contrib.auth.models import User
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        print('✅ Admin user created: username=admin, password=admin123')
    else:
        print('ℹ️ Admin user already exists')
except Exception as e:
    print(f'⚠️ Admin creation failed: {e}')
"

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "✅ Starting server on port $PORT..."
exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --access-logfile - --error-logfile - oj_project.wsgi:application