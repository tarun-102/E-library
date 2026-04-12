import os
import dj_database_url
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-kv6ok0txp86i3avrbq1as-m9)ya#*-=e2x72!wcu9tv#=&dhkd",
)

DEBUG = os.environ.get("DEBUG", "True").lower() in ("1", "true", "yes")

# Comma-separated override, e.g. "localhost,127.0.0.1,.vercel.app"
_allowed = os.environ.get("ALLOWED_HOSTS", "").strip()
if _allowed:
    ALLOWED_HOSTS = [h.strip() for h in _allowed.split(",") if h.strip()]
else:
    ALLOWED_HOSTS = [".vercel.app", "127.0.0.1", "localhost"]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'library',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # <--- YE LINE SABSE ZAROORI HAI
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'elibrary.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'elibrary.wsgi.application'

# Use DATABASE_URL (e.g. Neon) on serverless hosts — their filesystem is read-only, so SQLite cannot work.
_database_url = os.environ.get("DATABASE_URL", "").strip()
_on_vercel = bool(os.environ.get("VERCEL"))
if _database_url:
    DATABASES = {"default": dj_database_url.parse(_database_url, conn_max_age=600)}
elif _on_vercel:
    raise ImproperlyConfigured(
        "On Vercel the filesystem is read-only, so SQLite cannot be used for writes. "
        "Add DATABASE_URL (PostgreSQL, e.g. Neon) under Project Settings - Environment Variables, "
        "redeploy, then run migrations against that database "
        "(for example: vercel env pull, then python manage.py migrate with DATABASE_URL set)."
    )
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = []

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

_csrf_origins = os.environ.get("CSRF_TRUSTED_ORIGINS", "").strip()
if _csrf_origins:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins.split(",") if o.strip()]
else:
    CSRF_TRUSTED_ORIGINS = []
    if DEBUG:
        CSRF_TRUSTED_ORIGINS.extend(
            [
                "http://127.0.0.1:8000",
                "http://localhost:8000",
            ]
        )
    _vercel_url = os.environ.get("VERCEL_URL", "").strip()
    if _vercel_url:
        CSRF_TRUSTED_ORIGINS.append(f"https://{_vercel_url}")

# Behind Vercel’s proxy, request.is_secure() uses X-Forwarded-Proto
if _on_vercel:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static Files Setup
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media Files (Images)
MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'