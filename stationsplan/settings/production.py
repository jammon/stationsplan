from .base import *
import os
import sys

DEBUG = False

ALLOWED_HOSTS = ['.stationsplan.de']
STATIC_ROOT = '/var/www/stationsplan/htdocs/static/'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

SECRETS_DIR = os.path.join(PARENT_OF_BASE_DIR, "secrets")
# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'stationsplan',
        'USER': 'stationsplan',
        'PASSWORD': read_secret(os.path.join(SECRETS_DIR, "db-password.txt"),
                                "mysql password"),
        'TEST': {
            'NAME': 'stationsplantest',
        },
        'CONN_MAX_AGE': 5,
    }
}
if 'test' in sys.argv:
    DATABASES['default']['USER'] = 'stationsplantest'
    DATABASES['default']['PASSWORD'] = 'LavRagJavEvot>'

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
            'filename': '/var/www/stationsplan/priv/logs/debug.log',
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
