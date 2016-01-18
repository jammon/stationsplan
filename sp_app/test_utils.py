# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
from django.contrib.auth.models import User
from unittest import TestCase
from datetime import date

from .utils import (get_past_changes, last_day_of_month,
                    changes_for_month_as_json,
                    get_for_company, PopulatedTestCase)
from .models import Company, Person, Ward, ChangeLogging


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
            name="Person A", shortname="P-A", company=self.company)
        person_a.departments.add(self.department)
        person_b = Person.objects.create(
            name="Person B", shortname="P-B", company=self.company)
        person_b.departments.add(self.department)
        person_c = Person.objects.create(
            name="Person C", shortname="P-C", company=self.company,
            end_date=date(2015, 9, 30))
        person_c.departments.add(self.department)
        self.nightshift = Ward.objects.create(
            name="Nightshift", shortname="N", max=1, min=1,
            nightshift=True, everyday=True, continued=False, on_leave=False,
            company=self.company)
        user = User.objects.create(username='Mr. User', password='123456')
        data = (
            (person_a, self.ward_a, date(2015, 9, 7), True),
            (person_b, self.ward_a, date(2015, 9, 7), True),  # add to ward a
            (person_b, self.ward_a, date(2015, 9, 9), False),  # and remove
            (person_c, self.ward_a, date(2015, 9, 7), True),  # leaving in Sept.
            (person_a, self.nightshift, date(2015, 9, 14), True),  # not to be continued
            (person_a, self.ward_a, date(2015, 10, 1), False),
            (person_a, self.ward_b, date(2015, 10, 5), True),
            (person_b, self.ward_a, date(2015, 10, 5), True),
            (person_a, self.ward_a, date(2015, 10, 31), True),
            (person_b, self.ward_a, date(2015, 11, 6), False),
        )
        for (person, ward, day, added) in data:
            ChangeLogging.objects.create(
                person=person, ward=ward, day=day, added=added,
                company=self.company, user=user)

    def test_changes_for_month(self):
        result = changes_for_month_as_json(date(2015, 10, 1), [self.ward_a])
        self.assertEqual(
            json.loads(result),
            [{'person': "P-A", 'ward': "A", 'day': "20151001", 'action': "remove"},
             {'person': "P-B", 'ward': "A", 'day': "20151005", 'action': "add"},
             {'person': "P-A", 'ward': "A", 'day': "20151031", 'action': "add"},
             ])

    def test_get_past_changes(self):
        result = get_past_changes(
            date(2015, 10, 1), [self.ward_a, self.nightshift])
        self.assertEqual(
            result,
            [{'person': "P-A", 'ward': "A", 'day': "20151001",
              'action': "add"}])

    def test_description(self):
        c = ChangeLogging.objects.get(ward=self.nightshift)
        self.assertEqual(
            c.description,
            "Mr. User: Person A ist am 14.09.2015 für Nightshift eingeteilt")
        c = ChangeLogging.objects.get(day=date(2015, 10, 31))
        self.assertEqual(
            c.description,
            "Mr. User: Person A ist ab 31.10.2015 für Ward A eingeteilt")
        c = ChangeLogging.objects.get(day=date(2015, 11, 6))
        self.assertEqual(
            c.description,
            "Mr. User: Person B ist ab 06.11.2015 für Ward A nicht mehr eingeteilt")


class TestGetForCompany(TestCase):

    def test_get_for_company(self):
        company_a = Company.objects.create(name="Company A", shortname="C-A")
        company_b = Company.objects.create(name="Company B", shortname="C-B")
        Person.objects.create(name="Anna Smith", shortname="Smith",
                              company=company_a)
        Person.objects.create(name="Bob Smythe", shortname="Smythe",
                              company=company_a)
        Person.objects.create(name="Peter Smith", shortname="Smith",
                              company=company_b)

        class Request:
            session = {'company_id': company_a.id}
        smith = get_for_company(Person, Request(), shortname="Smith")
        self.assertEqual(smith.name, "Anna Smith")
