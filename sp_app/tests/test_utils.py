# -*- coding: utf-8 -*-
from datetime import date
from django.conf import settings

from sp_app.utils import get_first_of_month, last_day_of_month


def test_get_first_of_month():
    data = (
        ("201510", date(2015, 10, 1)),
        ("20151001", date(2015, 10, 1)),
        ("20151031", date(2015, 10, 1)),
    )
    for given, expected in data:
        assert expected == get_first_of_month(given)


def test_ldom():
    data = (
        (date(2015, 1, 1), date(2015, 1, 31)),
        (date(2015, 1, 31), date(2015, 1, 31)),
        (date(2015, 2, 1), date(2015, 2, 28)),
        (date(2015, 2, 28), date(2015, 2, 28)),
        (date(2016, 2, 1), date(2016, 2, 29)),
        (date(2016, 2, 29), date(2016, 2, 29)),
    )
    for given, expected in data:
        assert last_day_of_month(given) == expected


def test_email_settings():
    assert settings.EMAIL_AVAILABLE
    assert settings.EMAIL_HOST.endswith(".uberspace.de")
    assert settings.EMAIL_PORT == 587
    assert settings.EMAIL_HOST_USER.startswith("server@")
    assert len(settings.EMAIL_HOST_PASSWORD) > 5
    assert settings.EMAIL_USE_TLS
    assert not settings.EMAIL_USE_SSL
