from .base import *
import os

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '&df40)%pr4_d78+h=r!anx%3s!&8x!xgcnxphpoi(y7qk)3mb4'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []
STATIC_ROOT = os.path.join(BASE_DIR, "dev_static")

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

DJANGO_TEMPLATES['DIRS'] = []
DJANGO_TEMPLATES['APP_DIRS'] = True
