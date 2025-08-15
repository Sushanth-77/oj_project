#!/usr/bin/env bash
set -o errexit

echo "📦 Installing dependencies..."
pip install --no-cache-dir -r requirements.txt

echo "✅ Build completed quickly!"