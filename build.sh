#!/usr/bin/env bash
# exit on error
set -o errexit

# Make sure we have proper permissions (Linux/Unix)
chmod +x "$0" 2>/dev/null || true

echo "📦 Installing dependencies..."
# Install dependencies
pip install -r requirements.txt

echo "📁 Changing to Django project directory..."
# Change to the Django project directory (where manage.py is located)
cd oj_project/oj_project

echo "🔍 Checking Django setup..."
# Check if Django can import properly
python -c "import django; print('Django version:', django.get_version())"

echo "⚙️ Running Django checks..."
# Check for any obvious issues
python manage.py check || echo "⚠️  Django check had warnings, continuing..."

echo "📝 Creating migrations..."
# Create migrations (in case any are missing)
python manage.py makemigrations || echo "⚠️  No new migrations created"

echo "🗄️ Running migrations..."
# Run migrations
python manage.py migrate

echo "📦 Collecting static files..."
# Collect static files
python manage.py collectstatic --no-input

echo "✅ Build completed successfully!"