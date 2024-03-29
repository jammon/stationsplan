# -*- coding: utf-8 -*-
import re
from datetime import timedelta, datetime, date
from zoneinfo import ZoneInfo

TZ_BERLIN = ZoneInfo("Europe/Berlin")


def get_first_of_month(month=""):
    """Returns a date.
    'month' should be a string in the form of 'YYYYMM' or 'YYYYMMDD'.
    If 'month' is not given, it returns the current month.
    """
    if not month:
        return date.today().replace(day=1)
    if len(month) == len("YYYYMM"):
        return datetime.strptime(month, "%Y%m").date()
    return datetime.strptime(month, "%Y%m%d").date().replace(day=1)


def last_day_of_month(date):
    """Returns a date and expects a date."""
    return (
        date.replace(day=31)
        if date.month == 12
        else date.replace(month=date.month + 1, day=1) - timedelta(days=1)
    )


def post_with_company(request):
    if request.POST:
        post = request.POST.copy()
        post["company"] = request.session["company_id"]
        return post
    return None


def time_since(dt):
    """Return the timedelta between now and dt"""
    return datetime.now(TZ_BERLIN) - dt


def is_mobile(request):
    """Return True if the request comes from a mobile device."""

    MOBILE_AGENT_RE = re.compile(r".*(iphone|mobile|android)", re.IGNORECASE)
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    return bool(MOBILE_AGENT_RE.match(user_agent))
