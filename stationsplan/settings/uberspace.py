from .base import *  # noqa: F403
import os
import configparser

DEBUG = False

ALLOWED_HOSTS = [
    ".stationsplan.de",
    "stplan2.uber.space",
    "localhost",
    "127.0.0.1",
]
STATIC_ROOT = os.path.expanduser("~/html/static/")
STATICFILES_STORAGE = (
    "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
)

CONFIG_FILE = os.path.expanduser("~/.statplan.cnf")
DB_CONFIG_FILE = os.path.expanduser("~/.my.cnf")

config = configparser.ConfigParser()
config.read(CONFIG_FILE)
try:
    SECRET_KEY = config["django"]["key"]
except KeyError:
    if not config.has_section("django"):
        config["django"] = {}
    SECRET_KEY = config["django"]["key"] = random_string(50)
    with open(CONFIG_FILE, "w") as configfile:
        config.write(configfile)


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

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.expanduser("~/logs/stationsplan.log"),
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
