#!/usr/bin/env bash
set -o errexit

echo "📦 Installing dependencies..."
pip install --no-cache-dir -r requirements.txt

echo "🔧 Setting up environment..."
export PYTHONPATH="/app/oj_project:$PYTHONPATH"
export DJANGO_SETTINGS_MODULE=oj_project.settings

cd /app/oj_project

echo "📝 Creating migrations..."
python manage.py makemigrations

echo "🗄️ Running migrations..."
python manage.py migrate

echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

echo "✅ Build completed!"