from .base import *
import os
import sys

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

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
            'USER': 'stationsplantest',
            'PASSWORD': 'LavRagJavEvot>'
        }
    }
}
if 'test' in sys.argv:
    DATABASES['default']['USER'] = 'stationsplantest'
    DATABASES['default']['PASSWORD'] = 'LavRagJavEvot>'

SECRET_KEY = read_secret(os.path.join(SECRETS_DIR, "django-key.txt"),
                         "random characters to generate your secret key",
                         generate_secret=True)
