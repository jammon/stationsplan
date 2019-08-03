# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
from unittest import TestCase
from datetime import date

from .utils import (get_first_of_month, last_day_of_month,
                    get_for_company, get_holidays_for_company,
                    apply_changes, set_approved, get_last_changes,
                    PopulatedTestCase)
from .models import Company, Person, Ward, Holiday, Region, ChangeLogging


class TestFirstOfMonth(TestCase):

    def test_gfom(self):
        data = (
            ("201510", date(2015, 10, 1)),
            ("20151001", date(2015, 10, 1)),
            ("20151031", date(2015, 10, 1)),
        )
        for given, expected in data:
            got = get_first_of_month(given)
            self.assertEqual(
                got, expected,
                msg=f"get_first_of_month for {given} should be {expected}, got {got}")


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
                msg=f"Last day of month for {given} should be {expected}")


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


class TestGetHolidaysForCompany(PopulatedTestCase):

    def test_get_holidays_for_company(self):
        weihnachten = Holiday.objects.create(
            name='Weihnachten', date=date(2017, 12, 25))
        neujahr = Holiday.objects.create(
            name='Neujahr', date=date(2018, 1, 1))
        dreikoenig = Holiday.objects.create(
            name='Dreikönig', date=date(2018, 1, 6))
        testregion = Region.objects.create(
            name="Testregion", shortname="Test")
        testregion.holidays.add(weihnachten, neujahr)
        self.company.region = testregion
        self.company.save()

        holidays = get_holidays_for_company(self.company.id)
        self.assertEqual(holidays['20171225'], 'Weihnachten')
        self.assertEqual(holidays['20180101'], 'Neujahr')
        self.assertNotIn('20180106', holidays)

        self.company.extra_holidays.add(dreikoenig)
        holidays = get_holidays_for_company(self.company.id)
        self.assertEqual(len(holidays), 3)
        self.assertEqual(holidays['20180106'], 'Dreikönig')


class TestApplyChanges(PopulatedTestCase):

    def test_apply_1_change(self):
        day = '20160328'
        continued = True
        persons = [{'id': self.person_a.id, 'action': 'add'}]
        cls = apply_changes(self.user, company_id=self.company.id,
                            day=day, ward_id=self.ward_a.id,
                            continued=continued, persons=persons)
        self.assertEqual(len(cls), 1)
        self.assertContainsDict(
            cls[0],
            {"person": self.person_a.id, "ward":self.ward_a.id,
             "action": "add", "continued": True, "day": "20160328"})

    def test_apply_2_changes(self):
        day = '20160328'
        continued = True
        persons = [{'id': self.person_a.id, 'action': 'add'},
                   {'id': self.person_b.id, 'action': 'add'}]
        cls = apply_changes(self.user, company_id=self.company.id,
                            day=day, ward_id=self.ward_a.id,
                            continued=continued, persons=persons)
        self.assertEqual(len(cls), 2)
        self.assertContainsDict(
            cls[0],
            {"person": self.person_a.id, "ward":self.ward_a.id,
             "action": "add", "continued": True, "day": "20160328"})
        self.assertContainsDict(
            cls[1],
            {"person": self.person_b.id, "ward":self.ward_a.id,
             "action": "add", "continued": True, "day": "20160328"})

    def test_apply_2_changes_nonsensical(self):
        """ The second change doesn't make sense, should not be returned
        """
        day = '20160328'
        continued = True
        persons = [{'id': self.person_a.id, 'action': 'add'},
                   {'id': self.person_b.id, 'action': 'remove'}]
        cls = apply_changes(self.user, company_id=self.company.id,
                            day=day, ward_id=self.ward_a.id,
                            continued=continued, persons=persons)
        self.assertEqual(len(cls), 1)
        self.assertContainsDict(
            cls[0],
            {"person": self.person_a.id, "ward":self.ward_a.id,
             "action": "add", "continued": True, "day": "20160328"})


class TestSetApproved(PopulatedTestCase):

    def test_set_approved(self):
        def test_ward(ward_id, approval):
            ward = get_for_company(Ward, company_id=self.company.id,
                                   shortname=ward_id)
            self.assertEqual(ward.approved, approval)

        res = set_approved(['A', 'B'], '20170401', self.company.id)
        self.assertEqual(res, {'wards': ['A', 'B'], 'approved': '20170401'})
        test_ward('A', date(2017, 4, 1))
        test_ward('B', date(2017, 4, 1))

        res = set_approved(['A'], False, self.company.id)
        self.assertEqual(res, {'wards': ['A'], 'approved': False})
        test_ward('A', None)
        test_ward('B', date(2017, 4, 1))


class TestGetLastChanges(PopulatedTestCase):

    def test_get_last_changes(self):
        c_dict = dict(
            company=self.company, user_id=1, person=self.person_a,
            ward=self.ward_a, added=True, continued=False)
        c1 = ChangeLogging.objects.create(day=date(2017, 10, 27), **c_dict)
        c2 = ChangeLogging.objects.create(day=date(2017, 10, 28), **c_dict)
        c3 = ChangeLogging.objects.create(day=date(2017, 10, 29), **c_dict)

        response = get_last_changes(self.company.id, c1.pk)
        content = json.loads(response.content)
        self.assertEqual(len(content['cls']), 2)
        self.assertEqual(content['last_change']['pk'], c3.pk)

        response = get_last_changes(self.company.id, c2.pk)
        content = json.loads(response.content)
        self.assertEqual(len(content['cls']), 1)
        self.assertEqual(content['last_change']['pk'], c3.pk)


class TestAssertContainsDict(PopulatedTestCase):

    def test_assertContainsDict(self):
        self.assertContainsDict({'a': 1, 'b': 2}, {'a': 1})
        with self.assertRaises(AssertionError):
            self.assertContainsDict({'a': 2}, {'a': 1})
