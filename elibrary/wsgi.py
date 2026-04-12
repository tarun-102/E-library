"""
WSGI config for elibrary project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "elibrary.settings")

application = get_wsgi_application()

# Vercel fallback SQLite lives in /tmp; apply migrations once per process (no separate deploy step).
from django.conf import settings  # noqa: E402

if getattr(settings, "VERCEL_EPHEMERAL_SQLITE", False):
    from django.core.management import call_command  # noqa: E402

    call_command("migrate", "--noinput", verbosity=0)

from library.catalog_seed import ensure_sample_books  # noqa: E402

ensure_sample_books()
