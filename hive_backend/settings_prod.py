"""
Production settings for hive_backend project.
This file extends base settings with production-specific configurations.
"""
from .settings import *
import os

# Security settings for production
DEBUG = False
SECRET_KEY = os.getenv('SECRET_KEY')

if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable must be set in production")

# Allowed hosts - must include your domain
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS if host.strip()]

# Database - uses environment variables from Digital Ocean
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# CORS settings for production
# Get from environment variable, or use default EC2 frontend URL
cors_origins_env = os.getenv('CORS_ALLOWED_ORIGINS', '').strip()
if cors_origins_env:
    CORS_ALLOWED_ORIGINS = [origin.strip() for origin in cors_origins_env.split(',') if origin.strip()]
else:
    # Default: EC2 frontend URL (port 3000)
    # This will be used if CORS_ALLOWED_ORIGINS is not set in environment
    ec2_domain = os.getenv('EC2_DOMAIN', 'ec2-52-59-134-106.eu-central-1.compute.amazonaws.com')
    CORS_ALLOWED_ORIGINS = [f'http://{ec2_domain}:3000']

csrf_origins_env = os.getenv('CSRF_TRUSTED_ORIGINS', '').strip()
if csrf_origins_env:
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in csrf_origins_env.split(',') if origin.strip()]
else:
    # Default: EC2 frontend URL (port 3000)
    ec2_domain = os.getenv('EC2_DOMAIN', 'ec2-52-59-134-106.eu-central-1.compute.amazonaws.com')
    CSRF_TRUSTED_ORIGINS = [f'http://{ec2_domain}:3000']

CORS_ALLOW_CREDENTIALS = True

# Security settings
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True') == 'True'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

