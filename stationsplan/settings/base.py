"""
Django settings for stationsplan project.
"""
import configparser
import os
import string
import sys
import time
from pathlib import Path

from stationsplan.utils import random_string


# Build paths inside the project like this: BASE_DIR / "path/file.ext"
BASE_DIR = Path(__file__).resolve().parent.parent.parent

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
try:
    SECRET_KEY = config["django"]["key"]
except KeyError:
    if not config.has_section("django"):
        config["django"] = {}
    SECRET_KEY = config["django"]["key"] = random_string(50)
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

# Application definition
INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "sp_app",
)

MIDDLEWARE = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
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
# DJANGO_TEMPLATES will be changed in specialized settings
TEMPLATES = [
    DJANGO_TEMPLATES,
]


WSGI_APPLICATION = "stationsplan.wsgi.application"


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

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
