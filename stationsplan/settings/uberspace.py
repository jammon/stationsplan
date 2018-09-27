from .base import *  # noqa: F403
import os
from ConfigParser import ConfigParser, NoSectionError

DEBUG = False

ALLOWED_HOSTS = [
    '.stationsplan.de',
    'stplan2.uberspace.de',
    'localhost',
    '127.0.0.1',
]
STATIC_ROOT = os.path.expanduser('~/html/static/')
STATICFILES_STORAGE = \
    'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

CONFIG_FILE = os.path.expanduser('~/.statplan.cnf')
DB_CONFIG_FILE = os.path.expanduser('~/.my.cnf')

config = ConfigParser()
config.read(CONFIG_FILE)
try:
    SECRET_KEY = config.get('django', 'key')
except (KeyError, NoSectionError):
    if not config.has_section('django'):
        config.add_section('django')
    SECRET_KEY = random_string(50)
    config.set('django', 'key', SECRET_KEY)
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)


db_config = ConfigParser()
with open(DB_CONFIG_FILE) as db_conf_file:
    db_config.readfp(db_conf_file)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': db_config.get('client', 'user'),
        'USER': db_config.get('client', 'user'),
        'PASSWORD': db_config.get('client', 'password'),
        'TEST': {
            'NAME': 'statplan_test',
        },
        'CONN_MAX_AGE': 5,
    }
}


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
            'filename': os.path.expanduser('~/logs/stationsplan.log'),
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
