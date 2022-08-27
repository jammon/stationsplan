"""
Django settings for stationsplan project.
"""
import configparser
import os
import string
import sys
import time
from pathlib import Path, PosixPath
from random import choice

from stationsplan.utils import random_string


# Build paths inside the project like this: BASE_DIR / "path/file.ext"
BASE_DIR = Path(__file__).resolve().parent.parent

TESTING = False
if (
    len(sys.argv) >= 2
    and sys.argv[0].endswith("manage.py")
    and sys.argv[1] == "test"
):
    TESTING = True
if "pytest" in sys.argv[0].lower():
    TESTING = True
if TESTING:
    PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)

VERSION = time.strftime(
    "%Y-%m-%d", time.gmtime(os.path.getmtime(BASE_DIR / ".git"))
)

CONFIG_FILE = BASE_DIR / ".statplan.cnf"
config = configparser.ConfigParser(interpolation=None)
config.read(CONFIG_FILE)

# Server type: "dev", "staging" or "production"
SERVER_TYPE = config["server"]["type"]
assert SERVER_TYPE in ("dev", "production", "staging")

# Server dependant
SITE_ID = {"dev": 1, "production": 2, "staging": 3}[SERVER_TYPE]
ALLOWED_HOSTS = {
    "dev": [],
    "production": [
        ".stationsplan.de",
        "stplan2.uber.space",
        "localhost",
        "127.0.0.1",
    ],
    "staging": ["stpst.uber.space", "localhost", "127.0.0.1"],
}[SERVER_TYPE]

if SERVER_TYPE == "dev":
    DEBUG = True
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
    STATIC_ROOT = BASE_DIR / "dev_static"
    LOG_FILE = BASE_DIR / "debug.log"
else:
    DEBUG = False
    USER_HOME = PosixPath("~").expanduser()

    DB_CONFIG_FILE = USER_HOME / ".my.cnf"
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

    STATIC_ROOT = USER_HOME / "html" / "static"
    STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
    )

    LOG_FILE = USER_HOME / "logs" / "stationsplan.log"

    USE_X_FORWARDED_HOST = True

    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "unix://" + str(Path.home() / ".redis/sock?db=0"),
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
        }
    }
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "default"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "{levelname} - {asctime} - {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": LOG_FILE,
            "formatter": "simple",
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

# Secret Key
try:
    SECRET_KEY = config["django"]["key"]
except KeyError:
    if not config.has_section("django"):
        config["django"] = {}
    SECRET_KEY = config["django"]["key"] = random_string(
        50, string.digits + string.ascii_letters
    )
    with open(CONFIG_FILE, "w") as configfile:
        config.write(configfile)

# E-Mail
try:
    EMAIL_HOST = config["mail"]["host"]
    EMAIL_PORT = int(config["mail"]["port"])
    EMAIL_HOST_USER = config["mail"]["host_user"]
    EMAIL_HOST_PASSWORD = config["mail"]["host_password"]
    EMAIL_USE_TLS = config["mail"].getboolean("use_tls")
    EMAIL_USE_SSL = config["mail"].getboolean("use_ssl")
    EMAIL_AVAILABLE = True
except KeyError:
    EMAIL_AVAILABLE = False

# Domain
try:
    DOMAIN = config["server"]["domain"]
except KeyError:
    DOMAIN = "https://stationsplan.de"

SERVER_EMAIL = config["server"]["mail"]
ADMINS = [("Admin Stationsplan", SERVER_EMAIL)]

# Application definition
INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django_jinja",
    "sp_app",
)

MIDDLEWARE = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.sites.middleware.CurrentSiteMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.security.SecurityMiddleware",
)

ROOT_URLCONF = "stationsplan.urls"

DJANGO_TEMPLATES = {
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "OPTIONS": {
        "context_processors": [
            "django.contrib.auth.context_processors.auth",
            "django.template.context_processors.debug",
            "django.template.context_processors.i18n",
            "django.template.context_processors.media",
            "django.template.context_processors.request",
            "django.template.context_processors.static",
            "django.template.context_processors.tz",
            "django.contrib.messages.context_processors.messages",
            "stationsplan.context_processors.app_version",
        ],
    },
}
JINJA_TEMPLATES = {
    "BACKEND": "django_jinja.backend.Jinja2",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {},
}

# DJANGO_TEMPLATES will be changed in specialized settings
TEMPLATES = [
    JINJA_TEMPLATES,
    DJANGO_TEMPLATES,
]

if SERVER_TYPE == "dev":
    DJANGO_TEMPLATES["DIRS"] = []
    DJANGO_TEMPLATES["APP_DIRS"] = True
    INSTALLED_APPS += ("debug_toolbar",)
    MIDDLEWARE = (
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    ) + MIDDLEWARE
    INTERNAL_IPS = ("127.0.0.1", "localhost")

elif SERVER_TYPE in ("production", "staging"):
    DJANGO_TEMPLATES["OPTIONS"]["loaders"] = [
        (
            "django.template.loaders.cached.Loader",
            [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
        ),
    ]

from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse

from jinja2 import Environment


def environment(**options):
    env = Environment(**options)
    env.globals.update(
        {
            "static": staticfiles_storage.url,
            "url": reverse,
        }
    )
    return env


WSGI_APPLICATION = "stationsplan.wsgi.application"


DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = "de-de"

TIME_ZONE = "Europe/Berlin"

USE_I18N = True

USE_TZ = True
LOCALE_PATHS = (BASE_DIR / "locale",)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = "/static/"

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    # other finders..
)

LOGIN_URL = "/login"
LOGIN_REDIRECT_URL = "/plan"


def read_secret(secret_file_name, content_description, generate_secret=False):
    try:
        with open(secret_file_name) as f:
            return f.read().strip()
    except IOError:
        pass
    if generate_secret:
        try:
            secret = "".join(
                [
                    choice(string.ascii_letters + string.digits)
                    for i in range(50)
                ]
            )
            with open(secret_file_name, "w") as f:
                f.write(secret)
            return secret
        except IOError:
            pass
    error_message = "Please create a file named '%s' with %s!" % (
        secret_file_name,
        content_description,
    )
    raise Exception(error_message)
