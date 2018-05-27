from .base import *  # noqa: F403
import os
import configparser

DEBUG = False

ALLOWED_HOSTS = [
    '.stationsplan.de',
    'statplan.uberspace.de',
]
STATIC_ROOT = os.path.expanduser('~/stationsplan/static/')
STATICFILES_STORAGE = \
    'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

CONFIG_FILE = os.path.expanduser('~/.statplan.cnf')
DB_CONFIG_FILE = os.path.expanduser('~/.my.cnf')

config = configparser.ConfigParser()
config.read(CONFIG_FILE)
try:
    SECRET_KEY = config['django']['key']
except KeyError:
    if not config.has_section('django'):
        config['django'] = {}
    SECRET_KEY = config['django']['key'] = random_string(50)
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)


db_config = configparser.ConfigParser()
with open(DB_CONFIG_FILE) as db_conf_file:
    db_config.read_file(db_conf_file)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'statplan',
        'USER': db_config['client']['user'],
        'PASSWORD': db_config['client']['password'],
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
