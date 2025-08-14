# EMERGENCY SETTINGS - USE SQLITE AS FALLBACK
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-5v=pi38z*mjkv8xn#b!e6gt1)=46qdw2&8_@^@87(c)wdhmdj3')
DEBUG = True  # TEMPORARILY SET TO TRUE FOR DEBUGGING
ALLOWED_HOSTS = ['*']  # ALLOW ALL FOR NOW

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'authentication',
    'core',
    'compiler',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'oj_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
            BASE_DIR / 'authentication' / 'templates',
            BASE_DIR / 'core' / 'templates',
            BASE_DIR / 'compiler' / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'oj_project.wsgi.application'

# EMERGENCY: USE SQLITE INSTEAD OF POSTGRESQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/tmp/db.sqlite3',  # Use /tmp for Render
    }
}

# If PostgreSQL is available, use it
if os.environ.get('DATABASE_URL'):
    try:
        import dj_database_url
        DATABASES = {
            'default': dj_database_url.parse(
                os.environ.get('DATABASE_URL'),
                conn_max_age=600,
                conn_health_checks=True,
            )
        }
        print("✅ Using PostgreSQL")
    except:
        print("❌ PostgreSQL failed, using SQLite")

AUTH_PASSWORD_VALIDATORS = []  # DISABLE FOR NOW

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# DISABLE SECURITY FOR NOW
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
CSRF_TRUSTED_ORIGINS = ['*']

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyD9y3Gxll2GKFRnS6ErpxesSo2SuJOsyKs')