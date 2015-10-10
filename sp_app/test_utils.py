# from django.test import TestCase as DjangoTestCase
from unittest import TestCase
from datetime import date

from .utils import (get_past_changes, last_day_of_month, changes_for_month,
                    PopulatedTestCase)
from .models import Person, Ward, ChangingStaff


class TestLastDayOfMonth(TestCase):

    def test_ldom(self):
        data = (
            (date(2015, 1, 1), date(2015, 1, 31)),
            (date(2015, 1, 31), date(2015, 1, 31)),
            (date(2015, 2, 1), date(2015, 2, 28)),
            (date(2015, 2, 28), date(2015, 2, 28)),
            (date(2016, 2, 1), date(2016, 2, 29)),
            (date(2016, 2, 29), date(2016, 2, 29)),
        )
        for given, expected in data:
            self.assertEqual(
                last_day_of_month(given), expected,
                msg="Last day of month for {} should be {}".format(
                    given, expected))


class TestChanges(PopulatedTestCase):

    def setUp(self):
        super(TestChanges, self).setUp()
        person_a = Person.objects.create(
            name="Person A", shortname="P-A", department=self.department,
            company=self.company)
        person_b = Person.objects.create(
            name="Person B", shortname="P-B", department=self.department,
            company=self.company)
        person_c = Person.objects.create(
            name="Person C", shortname="P-C", department=self.department,
            company=self.company, end_date=date(2015, 9, 30))
        self.nightshift = Ward.objects.create(
            name="Nightshift", shortname="N", max=1, min=1,
            nightshift=True, everyday=True, continued=False, on_leave=False,
            company=self.company)
        data = (
            (person_a, self.ward_a, date(2015, 9, 7), True),
            (person_c, self.ward_a, date(2015, 9, 7), True),  # leaving in Sept.
            (person_a, self.nightshift, date(2015, 9, 14), True),  # not to be continued
            (person_a, self.ward_a, date(2015, 10, 2), False),
            (person_a, self.ward_b, date(2015, 10, 5), True),
            (person_b, self.ward_a, date(2015, 10, 5), True),
            (person_b, self.ward_a, date(2015, 11, 6), False),
        )
        ChangingStaff.objects.bulk_create([
            ChangingStaff(person=person, ward=ward, day=day, added=added)
            for (person, ward, day, added) in data
        ])

    def test_changes_for_month(self):
        result = changes_for_month(date(2015, 10, 1), [self.ward_a])
        self.assertEqual(
            result,
            [{'person': "P-A", 'ward': "A", 'day': "20151002", 'action': "remove"},
             {'person': "P-B", 'ward': "A", 'day': "20151005", 'action': "add"}])

    def test_get_past_changes(self):
        result = get_past_changes(date(2015, 10, 1), [self.ward_a, self.nightshift])
        self.assertEqual(
            result,
            [{'person': "P-A", 'ward': "A", 'day': "20151001", 'action': "add"}])
