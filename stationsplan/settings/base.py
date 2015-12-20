"""
Django settings for stationsplan project.

Generated by 'django-admin startproject' using Django 1.8.4.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PARENT_OF_BASE_DIR = os.path.dirname(BASE_DIR)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '&df40)%pr4_d78+h=r!anx%3s!&8x!xgcnxphpoi(y7qk)3mb4'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'compressor',
    'debug_toolbar',
    'debug_panel',
    'django_nose',
    'sp_app',
)

MIDDLEWARE_CLASSES = (
    'debug_panel.middleware.DebugPanelMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'stationsplan.urls'

DJANGO_TEMPLATES = {
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'OPTIONS': {
        'context_processors': [
            "django.contrib.auth.context_processors.auth",
            "django.template.context_processors.debug",
            "django.template.context_processors.i18n",
            "django.template.context_processors.media",
            "django.template.context_processors.request",
            "django.template.context_processors.static",
            "django.template.context_processors.tz",
            "django.contrib.messages.context_processors.messages",
        ],
    },
}
TEMPLATES = [DJANGO_TEMPLATES, ]

WSGI_APPLICATION = 'stationsplan.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'de-de'

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

USE_L10N = True

USE_TZ = True
LOCALE_PATHS = (os.path.join(BASE_DIR, 'locale'), )

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # other finders..
    'compressor.finders.CompressorFinder',
)

LOGIN_URL = "/login"
LOGIN_REDIRECT_URL = "/plan"

# Use nose to run all tests
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

# Tell nose to measure coverage on the 'foo' and 'bar' apps
# NOSE_ARGS = [
#     '--with-coverage',
#     '--cover-package=stationsplan,sp_app',
#     '--cover-html',
# ]


def read_secret(secret_file_name, content_description,
                generate_secret=False):
    try:
        with open(secret_file_name) as f:
            return f.read().strip()
    except IOError:
        pass
    if generate_secret:
        try:
            from random import choice
            import string
            secret = ''.join([choice(string.ascii_letters+string.digits)
                              for i in range(50)])
            with open(secret_file_name, 'w') as f:
                f.write(secret)
            return secret
        except IOError:
            pass
    error_message = ("Please create a file named '%s' with %s!"
                     % (secret_file_name, content_description))
    raise Exception(error_message)

DEBUG_TOOLBAR_PATCH_SETTINGS = False
