# -*- coding: utf-8 -*-
import json
from django.core.cache import cache
from unittest import TestCase
from datetime import date
from http import HTTPStatus

from .utils import (get_first_of_month, last_day_of_month,
                    get_for_company, get_holidays_for_company,
                    apply_changes, set_approved, get_last_change_response,
                    get_cached_last_change_pk, set_cached_last_change_pk,
                    PopulatedTestCase)
from .models import (Company, Department, Person, Ward, CalculatedHoliday,
                     Region, ChangeLogging)


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
                msg=f"get_first_of_month for {given} should be {expected}, "
                    f"got {got}")


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
        weihnachten = CalculatedHoliday.objects.create(
            name='Weihnachten', mode='abs', day=25, month=12)
        ostern = CalculatedHoliday.objects.create(
            name='Ostern', mode='rel', day=0)
        dreikoenig = CalculatedHoliday.objects.create(
            name='Dreikönig', mode='abs', day=6, month=1)
        testregion = Region.objects.create(
            name="Testregion", shortname="Test")
        testregion.calc_holidays.add(weihnachten, ostern)
        self.company.region = testregion
        self.company.save()

        holidays = [h.id for h in get_holidays_for_company(self.company.id)]
        self.assertIn(weihnachten.id, holidays)
        self.assertIn(ostern.id, holidays)
        self.assertNotIn(dreikoenig.id, holidays)


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
            {"person": self.person_a.shortname, "ward": self.ward_a.shortname,
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
            {"person": self.person_a.shortname, "ward": self.ward_a.shortname,
             "action": "add", "continued": True, "day": "20160328"})
        self.assertContainsDict(
            cls[1],
            {"person": self.person_b.shortname, "ward": self.ward_a.shortname,
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
            {"person": self.person_a.shortname,
             "ward": self.ward_a.shortname,
             "action": "add", "continued": True, "day": "20160328"})


class TestSetApproved(PopulatedTestCase):

    def do_test(self, ward_id, approval):
        ward = get_for_company(Ward, company_id=self.company.id,
                               shortname=ward_id)
        self.assertEqual(ward.approved, approval)

    def test_set_approved(self):
        res = set_approved(['A', 'B'], '20170401', [self.department.id])
        self.assertEqual(res.get('wards'), ['A', 'B'])
        self.assertEqual(res.get('approved'), '20170401')
        self.do_test('A', date(2017, 4, 1))
        self.do_test('B', date(2017, 4, 1))

        res = set_approved(['A'], False, [self.department.id])
        self.assertEqual(res.get('wards'), ['A'])
        self.assertEqual(res.get('approved'), False)
        self.do_test('A', None)
        self.do_test('B', date(2017, 4, 1))

    def test_wrong_department(self):
        department2 = Department.objects.create(
            name="Department 2", shortname="Dep2", company=self.company)
        ward_z = Ward.objects.create(
            name="Ward Z", shortname="Z", max=3, min=2,
            company=self.company)
        ward_z.departments.add(department2)
        res = set_approved(['Z'], '20170401', [self.department.id])
        self.assertFalse(res.get('wards'))
        self.assertEqual(res.get('not approved wards'), ['Z'])
        self.do_test('Z', None)


class TestGetLastChanges(PopulatedTestCase):

    def setUp(self):
        super(TestGetLastChanges, self).setUp()
        self.key = f"last_change_pk-{self.company.id}"
        cache.set(self.key, None)

    def test_get_cached_last_change_pk(self):
        self.assertIsNone(cache.get(self.key))
        self.assertIsNone(get_cached_last_change_pk(self.company.id))
        set_cached_last_change_pk("abcd", self.company.id)
        self.assertEqual(get_cached_last_change_pk(self.company.id), "abcd")
        self.assertEqual(cache.get(self.key), "abcd")

    def test_get_last_change_response(self):
        c_dict = dict(
            company=self.company, user_id=1, person=self.person_a,
            ward=self.ward_a, added=True, continued=False)
        c1 = ChangeLogging.objects.create(day=date(2017, 10, 27), **c_dict)
        c2 = ChangeLogging.objects.create(day=date(2017, 10, 28), **c_dict)
        c3 = ChangeLogging.objects.create(day=date(2017, 10, 29), **c_dict)

        response = get_last_change_response(self.company.id, c1.pk)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        content = json.loads(response.content)
        self.assertIn('cls', content)
        self.assertEqual(len(content['cls']), 2)
        self.assertEqual(content['last_change']['pk'], c3.pk)

        response = get_last_change_response(self.company.id, c2.pk)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        content = json.loads(response.content)
        self.assertEqual(len(content['cls']), 1)
        self.assertEqual(
            content['cls'][0],
            {'person': 'A',
             'ward': 'A',
             'day': '20171029',
             'action': 'add',
             'continued': False,
             'pk': c3.pk})
        self.assertEqual(content['last_change']['pk'], c3.pk)


class TestAssertContainsDict(PopulatedTestCase):

    def test_assertContainsDict(self):
        self.assertContainsDict({'a': 1, 'b': 2}, {'a': 1})
        with self.assertRaises(AssertionError):
            self.assertContainsDict({'a': 2}, {'a': 1})
