from __future__ import unicode_literals
from collections import defaultdict
from datetime import timedelta, datetime, date
from django.shortcuts import get_object_or_404
from django.test import TestCase
from .models import ChangeLogging, Ward, Person, Company, Department


def json_array(data):
    return '[' + ', '.join(d.json for d in data) + ']'


def get_past_changes(first_of_month, wards_ids):
    changes = ChangeLogging.objects.filter(
        day__gt=first_of_month-timedelta(days=153),  # five months back
        day__lt=first_of_month,
        ward_id__in=wards_ids,
        person__end_date__gt=first_of_month,
    ).order_by('change_time', 'id').values(
        'person__shortname', 'ward__shortname', 'day', 'added', 'continued')
    # hold the last time, a person was added to a ward
    past_changes = defaultdict(list)
    for c in changes:
        past_changes[(c['person__shortname'], c['ward__shortname'])].append(c)
    for l in past_changes.values():
        # sort by day
        l.sort(key=lambda x: x['day'])
        # delete changes that cancel themselves out
        while (len(l) > 1 and l[-2]['day'] == l[-2]['day'] and
               l[-2]['continued'] == l[-2]['continued']):
            del l[-2:]

    f_o_m = first_of_month.strftime('%Y%m%d')
    return [{'person': person,
             'ward': ward,
             'day': f_o_m,
             'action': 'add',
             'continued': True}
            for ((person, ward), c) in past_changes.items()
            if len(c) > 0 and c[-1]['added'] == c[-1]['continued']]


def changes_for_month_as_json(first_of_month, wards_ids):
    changes = ChangeLogging.objects.filter(
        day__gte=first_of_month,
        day__lte=last_day_of_month(first_of_month),
        ward_id__in=wards_ids,
    ).order_by('change_time', 'id')
    return json_array(changes)


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
        self.person_a = Person.objects.create(
            name="Person A", shortname="A", company=self.company)
        self.person_b = Person.objects.create(
            name="Person B", shortname="B", company=self.company)
        self.person_a.departments.add(self.department)
        self.person_b.departments.add(self.department)
        self.person_a.functions.add(self.ward_a, self.ward_b)
        self.person_b.functions.add(self.ward_a, self.ward_b)
