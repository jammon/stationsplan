from __future__ import unicode_literals
from datetime import timedelta, datetime, date
from django.shortcuts import get_object_or_404
from django.test import TestCase
from .models import Ward, Person, Company, Department


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


def get_for_company(klass, request, **kwargs):
    return get_object_or_404(
        klass, company__id=request.session['company_id'], **kwargs)


class PopulatedTestCase(TestCase):
    """TestCase with some prepared objects.
    These objects should not be altered in the tests.
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
