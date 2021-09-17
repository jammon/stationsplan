# -*- coding: utf-8 -*-
import json
import logging
import pytz

from datetime import timedelta, datetime, date
from django.contrib.auth.models import User
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.test import TestCase
from http import HTTPStatus
from numbers import Number
from .models import (
    Ward,
    Person,
    Company,
    Department,
    ChangeLogging,
    CalculatedHoliday,
    process_change,
)


def json_array(data):
    return f"[{', '.join(d.json for d in data)}]"


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


def get_for_company(klass, request=None, company_id="", **kwargs):
    """Return a model for this company

    Raises Http404 if not found
    """
    if request is None:
        return get_object_or_404(klass, company__id=company_id, **kwargs)
    return get_object_or_404(
        klass, company__id=request.session["company_id"], **kwargs
    )


def get_holidays_for_company(company_id):
    return CalculatedHoliday.objects.filter(regions__companies__id=company_id)


def apply_changes(user, company_id, day, ward_id, continued, persons):
    """Apply changes for this day and ward.
    Return a list of dicts of effective changes to be returned to the client
    'persons' is a list of dicts like
    {'id': <id>,
     'action': ‘add'|'remove'}
    """
    ward = get_for_company(Ward, company_id=company_id, id=ward_id)
    known_persons = {
        person.id: person
        for person in Person.objects.filter(
            company__id=company_id, id__in=(p["id"] for p in persons)
        )
    }
    data = dict(
        company_id=company_id,
        user=user,
        ward=ward,
        day=datetime.strptime(day, "%Y%m%d").date(),
        continued=continued,
        until=None,
    )
    if isinstance(continued, str):
        data["until"] = datetime.strptime(continued, "%Y%m%d").date()
        data["continued"] = True
    cls = []
    for p in persons:
        p_id = int(p["id"])
        # TODO: log error
        assert p_id in known_persons, f"{p_id} is not in the persons database"
        cl = ChangeLogging.objects.create(
            person=known_persons[p_id], added=p["action"] == "add", **data
        )
        cl_dict = process_change(cl)
        if cl_dict:
            cls.append(cl_dict)
    if len(cls):
        set_cached_last_change_pk(max(cl["pk"] for cl in cls), company_id)
    return cls


def set_approved(wards, approved, department_ids):
    """
    wards is [<ward.shortname>, ...],
    approved is False|<YYYYMMDD>, (False means unlimited approval)
    company_id is <company.id>
    """
    to_approve = Ward.objects.filter(
        departments__id__in=department_ids, shortname__in=wards
    )
    approval = (
        datetime.strptime(approved, "%Y%m%d").date() if approved else None
    )
    to_approve_sn = []
    for ward in to_approve:
        ward.approved = approval
        ward.save()
        to_approve_sn.append(ward.shortname)
    return {
        "wards": to_approve_sn,
        "approved": approved,
        "not approved wards": [
            ward for ward in wards if ward not in to_approve_sn
        ],
    }


def get_cached_last_change_pk(company_id):
    """Returns the pk of the last changelogging or None if not set"""
    return cache.get(f"last_change_pk-{company_id}")


def set_cached_last_change_pk(last_change_pk, company_id):
    """Sets the pk of the last changelogging"""
    return cache.set(f"last_change_pk-{company_id}", last_change_pk)


def get_last_change_response(company_id, last_change_pk):
    """Return a JsonResponse with the changes since last_change_pk
    and pk and elapsed time of the last change.
    """
    assert isinstance(last_change_pk, Number)
    _lc_pk = get_cached_last_change_pk(company_id)
    if _lc_pk and (_lc_pk == last_change_pk):
        # Nothing changed
        return JsonResponse({}, status=HTTPStatus.NOT_MODIFIED)

    # get all ChangeLoggings since and including last_change_pk
    cls = list(
        ChangeLogging.objects.filter(
            company_id=company_id, pk__gte=last_change_pk
        ).order_by("pk")
    )
    if len(cls) == 0:
        # Only older ChangeLoggings, so last_change_pk is wrong
        cls = [ChangeLogging.objects.order_by("pk").last()]
        if len(cls) == 0:
            # No ChangeLoggings
            logging.debug("No ChangeLoggings found")
            return JsonResponse({}, status=HTTPStatus.NOT_MODIFIED)
    if cls[0].pk == last_change_pk:
        if len(cls) == 1:
            # No newer ChangeLoggings
            return JsonResponse({}, status=HTTPStatus.NOT_MODIFIED)
        cls = cls[1:]
    last_cl = cls[-1]
    time_diff = datetime.now(pytz.utc) - last_cl.change_time
    if _lc_pk is None:
        # Set cache
        set_cached_last_change_pk(last_cl.pk, company_id)
    return JsonResponse(
        {
            "cls": [
                json.loads(cl.json) if cl.json else cl.toJson() for cl in cls
            ],
            "last_change": {
                "pk": last_cl.pk,
                "time": time_diff.days * 86400 + time_diff.seconds,
            },
        }
    )


class PopulatedTestCase(TestCase):
    """TestCase with some prepared objects."""

    def setUp(self):
        self.company = Company.objects.create(name="Company", shortname="Comp")
        self.department = Department.objects.create(
            name="Department 1", shortname="Dep1", company=self.company
        )
        self.ward_a = Ward.objects.create(
            name="Ward A",
            shortname="A",
            max=3,
            min=2,
            everyday=False,
            on_leave=False,
            company=self.company,
        )
        self.ward_a.departments.add(self.department)
        self.ward_b = Ward.objects.create(
            name="Ward B",
            shortname="B",
            max=2,
            min=1,
            everyday=False,
            on_leave=False,
            company=self.company,
        )
        self.ward_b.departments.add(self.department)
        self.person_a = Person.objects.create(
            name="Person A", shortname="A", company=self.company
        )
        self.person_b = Person.objects.create(
            name="Person B", shortname="B", company=self.company
        )
        self.person_a.departments.add(self.department)
        self.person_b.departments.add(self.department)
        self.person_a.functions.add(self.ward_a, self.ward_b)
        self.person_b.functions.add(self.ward_a, self.ward_b)
        self.user = User.objects.create(username="Mr. User", password="123456")

    def assertContainsDict(self, given, expected):
        for key, value in expected.items():
            self.assertEqual(
                given[key],
                value,
                f"{{ {repr(key)}: {repr(given[key])}, ...}} != "
                f"{{ {repr(key)}: {repr(value)}, ...}}",
            )
