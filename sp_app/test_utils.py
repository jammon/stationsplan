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
