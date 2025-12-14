"""
WSGI config for hive_backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Use production settings if DJANGO_ENV is set to production
if os.getenv('DJANGO_ENV') == 'production':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hive_backend.settings_prod')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hive_backend.settings')

application = get_wsgi_application()
