from __future__ import unicode_literals
import json
from datetime import timedelta, datetime, date
from django.shortcuts import get_object_or_404
from django.test import TestCase
from .models import ChangeLogging, Ward, Company, Department


def get_past_changes(first_of_month, wards_ids):
    past_changes = set()
    changes = ChangeLogging.objects.filter(
        day__gt=first_of_month-timedelta(days=92),  # three months back
        day__lt=first_of_month,
        ward_id__in=wards_ids,
        ward__continued=True,
        person__end_date__gt=first_of_month,
    ).order_by('change_time', 'id').values_list('json', flat=True)
    for c_json in changes:
        c = json.loads(c_json)
        if c['action']=='add':
            past_changes.add((c['person'], c['ward']))
        else:
            past_changes.discard((c['person'], c['ward']))
    fom = first_of_month.strftime('%Y%m%d')
    return [dict(person=person, ward=ward, day=fom, action='add')
            for person, ward in past_changes]


def changes_for_month_as_json(first_of_month, wards_ids):
    changes = ChangeLogging.objects.filter(
        day__gte=first_of_month,
        day__lte=last_day_of_month(first_of_month),
        ward_id__in=wards_ids,
    ).order_by('change_time', 'id').values_list('json', flat=True)
    return '[' + ','.join(changes) + ']'


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
