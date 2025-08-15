# oj_project/build_settings.py
# This file is used during Docker build to create migrations with SQLite

from .settings import *

# Force SQLite during build to create migration files
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/tmp/build_db.sqlite3',
    }
}

DEBUG = True
SECRET_KEY = 'build-time-key-not-used-in-production'

print("🔧 Using build settings with SQLite for migration creation")