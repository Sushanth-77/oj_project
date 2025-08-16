#!/usr/bin/env bash

echo "🚀 Starting app..."

# Verify compilers are available
echo "🔍 Checking compilers..."
gcc --version 2>/dev/null && echo "✅ GCC available" || echo "❌ GCC missing"
g++ --version 2>/dev/null && echo "✅ G++ available" || echo "❌ G++ missing"
javac -version 2>/dev/null && echo "✅ Java compiler available" || echo "❌ Java compiler missing"
node --version 2>/dev/null && echo "✅ Node.js available" || echo "❌ Node.js missing"
python3 --version 2>/dev/null && echo "✅ Python available" || echo "❌ Python missing"

cd /app/oj_project/oj_project

# Quick database check and migrate
echo "🔄 Running migrations..."
python manage.py migrate --run-syncdb || echo "Migration failed, continuing..."

# Create admin user quickly
echo "👤 Creating admin..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oj_project.settings')
django.setup()

try:
    from django.contrib.auth.models import User
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        print('✅ Admin created')
except:
    print('⚠️ Admin creation skipped')
" || echo "Admin creation failed"

# Collect static files quickly
echo "📦 Static files..."
python manage.py collectstatic --noinput --clear || echo "Static files skipped"

echo "✅ Starting server..."
exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 oj_project.wsgi:application