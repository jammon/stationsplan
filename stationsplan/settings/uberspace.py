import configparser
from pathlib import PosixPath

from .base import *  # noqa: F403

DEBUG = False

ALLOWED_HOSTS = [
    ".stationsplan.de",
    "stplan2.uber.space",
    "localhost",
    "127.0.0.1",
]
STATIC_ROOT = PosixPath("~/html/static/").expanduser()
STATICFILES_STORAGE = (
    "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
)

DB_CONFIG_FILE = PosixPath("~/.my.cnf").expanduser()

db_config = configparser.ConfigParser()
with open(DB_CONFIG_FILE) as db_conf_file:
    db_config.read_file(db_conf_file)

db_username = db_config["client"]["user"]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": db_username,
        "USER": db_username,
        "PASSWORD": db_config["client"]["password"],
        "TEST": {
            "NAME": db_username + "_test",
        },
        "CONN_MAX_AGE": 5,
    }
}


DJANGO_TEMPLATES["OPTIONS"]["loaders"] = [
    (
        "django.template.loaders.cached.Loader",
        [
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ],
    ),
]

LOG_FILE = PosixPath("~/logs/stationsplan.log").expanduser()
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": LOG_FILE,
        },
    },
    "loggers": {
        "django.request": {
            "handlers": ["file"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}

USE_X_FORWARDED_HOST = True

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "unix:///home/stplan2/.redis/sock?db=0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
