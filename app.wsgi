"""
WSGI config for stationsplan project in production.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os
import site
import sys

site.addsitedir('/var/www/stationsplan/priv/venv/lib/python2.7/site-packages')

sys.path.insert(0, '/var/www/stationsplan/priv/stationsplan')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stationsplan.settings.production")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
