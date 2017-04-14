# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import timedelta, datetime, date
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.test import TestCase
from .models import (Ward, Person, Company, Department, ChangeLogging,
                     process_change)


def json_array(data):
    return '[' + ', '.join(d.json for d in data) + ']'


def get_first_of_month(month=''):
    """ Returns a date.
    'month' should be a string in the form of 'YYYYMM'.
    If 'month' is not given, it returns the current month.
    """
    try:
        return datetime.strptime(month, '%Y%m').date()
    except (TypeError, ValueError):
        return date.today().replace(day=1)


def last_day_of_month(date):
    """ Returns a date and expects a date.
    """
    return (date.replace(day=31)
            if date.month == 12
            else date.replace(month=date.month+1, day=1) - timedelta(days=1))


def get_for_company(klass, request=None, company_id='', **kwargs):
    if request is None:
        return get_object_or_404(
            klass, company__id=company_id, **kwargs)
    return get_object_or_404(
        klass, company__id=request.session['company_id'], **kwargs)


def apply_changes(user, company_id, day, ward, continued, persons):
    """ Apply changes for this day and ward.
    Return a list of dicts of effective changes to be returned to the client
    'persons' is a list of dicts like
    {'id': <shortname>,
     'action': ‘add'|'remove'}
    """
    ward = get_for_company(Ward, company_id=company_id, shortname=ward)
    assert ward is not None
    known_persons = {
        person.shortname: person for person in Person.objects.filter(
            company__id=company_id,
            shortname__in=(p['id'] for p in persons))}
    data = dict(company_id=company_id, user=user, ward=ward,
                day=datetime.strptime(day, '%Y%m%d').date(),
                continued=continued,
                until=None)
    if isinstance(continued, basestring):
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
    approved is False|<YYYYMMDD>,
    company_id is <company.id>
    """
    wards = Ward.objects.filter(company_id=company_id,
                                shortname__in=wards)
    approval = (datetime.strptime(approved, '%Y%m%d').date()
                if approved else None)
    for ward in wards:
        ward.approved = approval
        ward.save()
    return {'wards': [ward.shortname for ward in wards], 'approved': approved}


class PopulatedTestCase(TestCase):
    """TestCase with some prepared objects.
    """
    def setUp(self):
        self.company = Company.objects.create(name="Company", shortname="Comp")
        self.department = Department.objects.create(
            name="Department 1", shortname="Dep1", company=self.company)
        self.ward_a = Ward.objects.create(
            name="Ward A", shortname="A", max=3, min=2,
            nightshift=False, everyday=False, continued=True, on_leave=False,
            company=self.company)
        self.ward_a.departments.add(self.department)
        self.ward_b = Ward.objects.create(
            name="Ward B", shortname="B", max=2, min=1,
            nightshift=False, everyday=False, continued=True, on_leave=False,
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
