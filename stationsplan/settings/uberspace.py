from .base import *
import os

DEBUG = False

ALLOWED_HOSTS = [
    '.stationsplan.de',
    'django.jammon.lynx.uberspace.de',
]
STATIC_ROOT = '/home/jammon/projects/stationsplan/static/'
STATICFILES_STORAGE = \
    'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

SECRETS_DIR = os.path.join(PARENT_OF_BASE_DIR, "secrets")
# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'stationsplan.db',
    }
}

SECRET_KEY = read_secret(os.path.join(SECRETS_DIR, "django-key.txt"),
                         "random characters to generate your secret key",
                         generate_secret=True)

DJANGO_TEMPLATES['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/home/jammon/projects/logs/stationsplan.log',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

USE_X_FORWARDED_HOST = True
