# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from unittest import TestCase
from datetime import date

from .utils import (last_day_of_month,
                    get_for_company, apply_changes,
                    PopulatedTestCase)
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
        self.person_c = Person.objects.create(
            name="Person C", shortname="C", company=self.company,
            end_date=date(2015, 9, 30))
        self.person_c.departments.add(self.department)
        self.nightshift = Ward.objects.create(
            name="Nightshift", shortname="N", max=1, min=1,
            nightshift=True, everyday=True, continued=False, on_leave=False,
            company=self.company)

    def test_description(self):  # gehört nach test_models
        testdata = (
            (self.person_a, self.nightshift, date(2015, 9, 14), True, True,
             "Mr. User: Person A ist am 14.09.2015 für Nightshift eingeteilt"),
            (self.person_a, self.ward_a, date(2015, 10, 31), True, True,
             "Mr. User: Person A ist ab 31.10.2015 für Ward A eingeteilt"),
            (self.person_b, self.ward_a, date(2015, 11, 6), False, True,
             "Mr. User: Person B ist ab 06.11.2015 nicht mehr für Ward A "
             "eingeteilt"))

        for (person, ward, day, added, continued, expected) in testdata:
            cl = ChangeLogging(
                person=person, ward=ward, day=day, added=added,
                continued=continued, company=self.company, user=self.user)
            cl.make_description()
            self.assertEqual(cl.description, expected)


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


class TestApplyChanges(PopulatedTestCase):

    def test_apply_1_change(self):
        day = '20160328'
        continued = True
        persons = [{'id': 'A', 'action': 'add'}]
        cls = apply_changes(self.user, company_id=self.company.id,
                            day=day, ward=self.ward_a.shortname,
                            continued=continued, persons=persons)
        self.assertEqual(len(cls), 1)
        self.assertEqual(
            cls[0],
            {"person": "A", "ward": "A",
             "action": "add", "continued": True, "day": "20160328"})

    def test_apply_2_changes(self):
        day = '20160328'
        continued = True
        persons = [{'id': 'A', 'action': 'add'},
                   {'id': 'B', 'action': 'add'}]
        cls = apply_changes(self.user, company_id=self.company.id,
                            day=day, ward=self.ward_a.shortname,
                            continued=continued, persons=persons)
        self.assertEqual(len(cls), 2)
        self.assertEqual(
            cls[0],
            {"person": "A", "ward": "A",
             "action": "add", "continued": True, "day": "20160328"})
        self.assertEqual(
            cls[1],
            {"person": "B", "ward": "A",
             "action": "add", "continued": True, "day": "20160328"})

    def test_apply_2_changes_nonsensical(self):
        """ The second change doesn't make sense, should not be returned
        """
        day = '20160328'
        continued = True
        persons = [{'id': 'A', 'action': 'add'},
                   {'id': 'B', 'action': 'remove'}]
        cls = apply_changes(self.user, company_id=self.company.id,
                            day=day, ward=self.ward_a.shortname,
                            continued=continued, persons=persons)
        self.assertEqual(len(cls), 1)
        self.assertEqual(
            cls[0],
            {"person": "A", "ward": "A",
             "action": "add", "continued": True, "day": "20160328"})
