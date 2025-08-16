#!/usr/bin/env bash
set -o errexit

echo "📦 Installing dependencies..."
pip install --no-cache-dir -r requirements.txt

echo "🔄 Creating migrations..."
cd oj_project
python manage.py makemigrations --noinput

echo "✅ Build completed!"