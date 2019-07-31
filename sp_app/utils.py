# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytz
import json

from datetime import timedelta, datetime, date
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.test import TestCase
from .models import (Ward, Person, Company, Department, ChangeLogging,
                     Holiday, process_change)


def json_array(data):
    return f"[{', '.join(d.json for d in data)}]"


def get_first_of_month(month=''):
    """ Returns a date.
    'month' should be a string in the form of 'YYYYMM' or 'YYYYMMDD'.
    If 'month' is not given, it returns the current month.
    """
    if not month:
        return date.today().replace(day=1)
    if len(month) == len('YYYYMM'):
        return datetime.strptime(month, '%Y%m').date()
    return datetime.strptime(month, '%Y%m%d').date().replace(day=1)


def last_day_of_month(date):
    """ Returns a date and expects a date.
    """
    return (date.replace(day=31)
            if date.month == 12
            else date.replace(month=date.month + 1, day=1) - timedelta(days=1))


def get_for_company(klass, request=None, company_id='', **kwargs):
    if request is None:
        return get_object_or_404(
            klass, company__id=company_id, **kwargs)
    return get_object_or_404(
        klass, company__id=request.session['company_id'], **kwargs)


def get_holidays_for_company(company_id):
    holidays = Holiday.objects.filter(
        Q(regions__companies__id=company_id) |
        Q(companies__id=company_id))
    return dict((h.date.strftime('%Y%m%d'), h.name) for h in holidays)


def apply_changes(user, company_id, day, ward_id, continued, persons):
    """ Apply changes for this day and ward.
    Return a list of dicts of effective changes to be returned to the client
    'persons' is a list of dicts like
    {'id': <id>,
     'action': ‘add'|'remove'}
    """
    ward = get_for_company(Ward, company_id=company_id, id=ward_id)
    assert ward is not None
    known_persons = {
        person.id: person for person in Person.objects.filter(
            company__id=company_id,
            id__in=(p['id'] for p in persons))}
    data = dict(company_id=company_id, user=user, ward=ward,
                day=datetime.strptime(day, '%Y%m%d').date(),
                continued=continued,
                until=None)
    if isinstance(continued, str):
        data['until'] = datetime.strptime(continued, '%Y%m%d').date()
        data['continued'] = True
    cls = []
    for p in persons:
        assert p['id'] in known_persons, \
            "%s is not in the persons database" % p['id']
        cl = ChangeLogging.objects.create(
            person=known_persons[p['id']],
            added=p['action'] == 'add',
            **data)
        cl_dict = process_change(cl)
        if cl_dict:
            cls.append(cl_dict)
    return cls


def set_approved(wards, approved, company_id):
    """
    wards is [<ward.shortname>, ...],
    approved is False|<YYYYMMDD>, (False means unlimited approval)
    company_id is <company.id>
    """
    wards = Ward.objects.filter(company_id=company_id,
                                shortname__in=wards)
    # TODO: test for malformatted input
    approval = (datetime.strptime(approved, '%Y%m%d').date()
                if approved else None)
    for ward in wards:
        ward.approved = approval
        ward.save()
    return {'wards': [ward.shortname for ward in wards], 'approved': approved}


def get_last_changes(company_id, last_change_pk):
    """ Return a JsonResponse with the changes since last_change_pk
    and pk and elapsed time of the last change.

    TODO: Sending changes triggers more frequent updates
    """
    cls = list(ChangeLogging.objects.filter(
        company_id=company_id,
        pk__gt=last_change_pk
    ).order_by('pk'))
    if len(cls) == 0:
        return JsonResponse({})
    last_cl = cls[-1]
    time_diff = datetime.now(pytz.utc) - last_cl.change_time
    return JsonResponse({
        'cls': [json.loads(cl.json) or cl.toJson() for cl in cls],
        'last_change': {
            'pk': last_cl.pk,
            'time': time_diff.days * 86400 + time_diff.seconds,
        }
    })


class PopulatedTestCase(TestCase):
    """TestCase with some prepared objects.
    """
    def setUp(self):
        self.company = Company.objects.create(name="Company", shortname="Comp")
        self.department = Department.objects.create(
            name="Department 1", shortname="Dep1", company=self.company)
        self.ward_a = Ward.objects.create(
            name="Ward A", shortname="A", max=3, min=2,
            nightshift=False, everyday=False, on_leave=False,
            company=self.company)
        self.ward_a.departments.add(self.department)
        self.ward_b = Ward.objects.create(
            name="Ward B", shortname="B", max=2, min=1,
            nightshift=False, everyday=False, on_leave=False,
            company=self.company)
        self.ward_b.departments.add(self.department)
        self.person_a = Person.objects.create(
            name="Person A", shortname="A", company=self.company)
        self.person_b = Person.objects.create(
            name="Person B", shortname="B", company=self.company)
        self.person_a.departments.add(self.department)
        self.person_b.departments.add(self.department)
        self.person_a.functions.add(self.ward_a, self.ward_b)
        self.person_b.functions.add(self.ward_a, self.ward_b)
        self.user = User.objects.create(username='Mr. User', password='123456')

    def assertContainsDict(self, given, expected):
        msg = "{{ {0}: {1}, ...}} != {{ {0}: {2}, ...}}"
        for key, value in expected.items():
            self.assertEqual(
                given[key], value,
                msg.format(repr(key), repr(given[key]), repr(value)))
