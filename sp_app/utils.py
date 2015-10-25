from __future__ import unicode_literals
from django.test import TestCase
from .models import ChangingStaff, Ward, Company, Department
from datetime import timedelta


def get_past_changes(first_of_month, wards):
    past_changes = set()
    queryset = ChangingStaff.objects.filter(
        day__gt=first_of_month-timedelta(days=92),  # three months back
        day__lt=first_of_month,
        ward__in=wards,
        ward__continued=True,
        person__end_date__gt=first_of_month,
    ).order_by('day')
    for c in queryset:
        if c.added:
            past_changes.add((c.person, c.ward))
        else:
            past_changes.discard((c.person, c.ward))
    return [ChangingStaff(person=person, ward=ward,
                          day=first_of_month, added=True).toJson()
            for person, ward in past_changes]


def changes_for_month(first_of_month, wards):
    queryset = ChangingStaff.objects.filter(
        day__gte=first_of_month,
        day__lt=last_day_of_month(first_of_month),
        ward__in=wards,
    ).order_by('day')
    return [c.toJson() for c in queryset]


def last_day_of_month(date):
    return (date.replace(day=31)
            if date.month == 12
            else date.replace(month=date.month+1, day=1) - timedelta(days=1))


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
        self.ward_a.department.add(self.department)
        self.ward_b = Ward.objects.create(
            name="Ward B", shortname="B", max=2, min=1,
            nightshift=False, everyday=False, continued=True, on_leave=False,
            company=self.company)
        self.ward_b.department.add(self.department)