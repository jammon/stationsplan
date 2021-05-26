# -*- coding: utf-8 -*-
from datetime import date, datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from http import HTTPStatus
import json
import logging

from .utils import PopulatedTestCase
from .models import Ward, Employee, ChangeLogging, Planning, StatusEntry
from .business_logic import get_plan_data


class TestViewsAnonymously(TestCase):

    def test_view_redirects_to_login(self):
        """ Test if 'plan', 'functions' and 'password_change' redirect
            to login if not logged in
        """
        c = Client()
        for name, url in (
                ('plan', '/plan/'),
                ('functions', '/zuordnung'),
                ('password_change', 'password_change/')):
            response = c.get(reverse(name))
            self.assertEqual(response.status_code, HTTPStatus.FOUND, msg=name)
            # TODO: why does this fail for 'password_change'?
            if name != 'password_change':
                for mode, f in (('get', c.get), ('post', c.post)):
                    response = f(reverse(name), follow=True)
                    self.assertRedirects(response, '/login?next=' + url,
                                         msg_prefix=f'{mode} - {url}')

    def test_changes(self):
        """ Test if 'changes' return status HTTPStatus.FORBIDDEN if not logged in
        """
        c = Client()
        response = c.get(reverse('changes'), {})
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        response = c.post(reverse('changes'), {})
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)


class TestPlanData(PopulatedTestCase):
    """ Test business logic for views.plan """

    def test_get_plan_data(self):
        for start, end in (
                (date(2016, 1, 1), date(2016, 1, 31)),  # older than 1 mon
                (date(2016, 2, 1), date(2016, 3, 1)),  # less than 1 mon
                (date(2016, 1, 1), date(2016, 4, 15)),
                (date(2016, 1, 1), date(2016, 5, 31)),
                (date(2016, 4, 1), date(2016, 4, 30)),
                (date(2016, 4, 1), date(2016, 5, 31)),
                (date(2016, 5, 1), date(2016, 5, 31))):
            Planning.objects.create(
                company=self.company, person=self.person_a,
                ward=self.ward_a, start=start, end=end)
        plan_data = get_plan_data(
            {'department_ids': [self.department.id],
             'company_id': self.company.id},
            '201604')
        data = json.loads(plan_data['data'])
        plannings = data['plannings']
        for value, expected in zip(plannings, (
                {'start': '20160201', 'end': '20160301'},
                {'start': '20160101', 'end': '20160415'},
                {'start': '20160101', 'end': '20160531'},
                {'start': '20160401', 'end': '20160430'},
                {'start': '20160401', 'end': '20160531'},
                {'start': '20160501', 'end': '20160531'})):
            self.assertEqual(value['person'], self.person_a.id)
            self.assertEqual(value['ward'], self.ward_a.id)
            self.assertEqual(value['start'], expected['start'])
            self.assertEqual(value['end'], expected['end'])


class ViewsTestCase(PopulatedTestCase):

    def setUp(self):
        super(ViewsTestCase, self).setUp()
        self.user = User.objects.create_user(
            'user', 'user@domain.tld', 'password')
        self.employee = Employee.objects.create(
            user=self.user, company=self.company)
        self.employee.departments.add(self.department)
        self.client.login(username='user', password='password')
        self.DATA_FOR_CHANGE = {
            'day': '20160120',
            'ward_id': self.ward_a.id,
            'continued': False,
            'persons': [
                {'id': self.person_a.id, 'action': 'add', },
                {'id': self.person_b.id, 'action': 'remove', },
            ],
            'last_pk': 0}


class TestPlan(ViewsTestCase):
    """ Test views.plan """

    def test_plan(self):
        response = self.client.get('/plan/201604')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_other_entries(self):
        response = self.client.get('/dienste/201604')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.client.get('/tag/201604')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.client.get('/zuordnung')
        self.assertEqual(response.status_code, HTTPStatus.OK)


# Tests for sp_app.ajax

class TestChangeForbidden(ViewsTestCase):
    """ User without permission to add changes
    """

    def do_test(self, view, data):
        # Disable logging of "PermissionDenied",
        # so not to clutter debug.log
        logging.disable(logging.CRITICAL)
        response = self.client.post(
            reverse(view),
            data,
            "text/json",
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        logging.disable(logging.NOTSET)

    def test_changes(self):
        """ Test if 'changes' return status HTTPStatus.FORBIDDEN if not logged in
        """
        self.do_test('changes', json.dumps(self.DATA_FOR_CHANGE))

    def test_approval(self):
        """ Test if 'set_approved' return status HTTPStatus.FORBIDDEN if not logged in
        """
        self.do_test('set_approved', 'data')


class ViewsWithPermissionTestCase(ViewsTestCase):

    def setUp(self):
        super(ViewsWithPermissionTestCase, self).setUp()
        self.user.user_permissions.add(
            Permission.objects.get(codename='is_editor'))
        self.user = User.objects.get(pk=self.user.pk)  # -> permission cache


class TestChangeMore(ViewsWithPermissionTestCase):

    def test_with_valid_data(self):
        """ Test if post 'changes' creates the right ChangeLoggings and returns them
        """
        self.client.post(
            reverse('changes'),
            json.dumps(self.DATA_FOR_CHANGE),
            "text/json",
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        cls = ChangeLogging.objects.all().order_by('person__shortname')
        self.assertEqual(len(cls), 2)
        cl = cls[0]
        self.assertEqual(cl.company, self.company)
        self.assertEqual(cl.user, self.user)
        self.assertEqual(cl.person, self.person_a)
        self.assertEqual(cl.ward, self.ward_a)
        self.assertEqual(cl.day, date(2016, 1, 20))
        self.assertEqual(cl.added, True)
        self.assertEqual(cl.continued, False)
        self.assertEqual(
            cl.description,
            'user: Person A ist am 20.01.2016 für Ward A eingeteilt')
        self.assertContainsDict(
            json.loads(cl.json),
            {"action": "add",
             "person": self.person_a.shortname,
             "ward": self.ward_a.shortname,
             "day": "20160120", "continued": False})
        self.assertEqual(cl.version, 1)
        cl = cls[1]
        self.assertEqual(cl.person, self.person_b)
        self.assertEqual(cl.ward, self.ward_a)
        self.assertEqual(cl.day, date(2016, 1, 20))
        self.assertEqual(cl.added, False)
        self.assertEqual(cl.continued, False)
        self.assertEqual(
            cl.description,
            'user: Person B ist am 20.01.2016 nicht mehr für Ward A '
            'eingeteilt')
        self.assertContainsDict(
            json.loads(cl.json),
            {"action": "remove",
             "person": self.person_b.shortname,
             "ward": self.ward_a.shortname,
             "day": "20160120", "continued": False})
        self.assertEqual(cl.version, 1)


class TestChangeApproval(ViewsWithPermissionTestCase):

    def test_change_approved(self):
        """ Test if post 'set_approved' sets approvals
        """
        self.client.post(
            reverse('set_approved'),
            json.dumps({'wards': ['A', 'B'], 'date': '20170414'}),
            "text/json",
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        stat = StatusEntry.objects.order_by('-pk').first()
        self.assertEqual(stat.content, 'user: A, B ist bis 20170414 sichtbar')
        for ward_id in 'AB':
            ward = Ward.objects.get(shortname=ward_id)
            self.assertEqual(ward.approved, date(2017, 4, 14))

        self.client.post(
            reverse('set_approved'),
            json.dumps({'wards': ['A'], 'date': False}),
            "text/json",
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        stat = StatusEntry.objects.order_by('-pk').first()
        self.assertEqual(stat.content, 'user: A ist unbegrenzt sichtbar')
        ward = Ward.objects.get(shortname='A')
        self.assertEqual(ward.approved, None)
        ward = Ward.objects.get(shortname='B')
        self.assertEqual(ward.approved, date(2017, 4, 14))


class TestChangeHistory(ViewsTestCase):
    """ Get the change history for a day and ward
    """
    expected = [
        {'user': 'Heinz Müller', 'person': 'B', 'ward': 'A',
         'day': '2020-04-24', 'added': False, 'continued': False,
         'until': None},
        {'user': 'Heinz Müller', 'person': 'B', 'ward': 'A',
         'day': '2020-04-24', 'added': True, 'continued': True,
         'until': '2020-04-30'},
        {'user': 'user', 'person': 'A', 'ward': 'A',
         'day': '2020-04-20', 'added': True, 'continued': True,
         'until': '2020-04-24'},
        {'user': 'user', 'person': 'A', 'ward': 'A',
         'day': '2020-04-10', 'added': False, 'continued': True,
         'until': None},
        {'user': 'user', 'person': 'A', 'ward': 'A',
         'day': '2020-04-01', 'added': True, 'continued': True,
         'until': None},
    ]

    def _apply_changes(self):
        user_with_name = User.objects.create_user(
            'hmueller', 'user@domain.tld', 'password',
            first_name='Heinz', last_name='Müller')
        employee = Employee.objects.create(
            user=user_with_name, company=self.company)
        employee.departments.add(self.department)
        data = (
            # ongoing assignment
            (self.user, self.person_a, self.ward_a, date(2020, 4, 1), True,
                True, None, datetime(2020, 3, 1, 10)),
            # stop it
            (self.user, self.person_a, self.ward_a, date(2020, 4, 10), False,
                True, None, datetime(2020, 3, 1, 10, 10)),
            # just some time until today
            (self.user, self.person_a, self.ward_a, date(2020, 4, 20), True,
                True, date(2020, 4, 24), datetime(2020, 3, 1, 10, 20)),
            # just some time from today
            (user_with_name, self.person_b, self.ward_a, date(2020, 4, 24),
                True, True, date(2020, 4, 30), datetime(2020, 3, 1, 10, 30)),
            # but not today
            (user_with_name, self.person_b, self.ward_a, date(2020, 4, 24),
                False, False, None, datetime(2020, 3, 1, 10, 40)),
            # different day
            (user_with_name, self.person_b, self.ward_a, date(2020, 4, 25),
                False, False, None, datetime(2020, 3, 1, 10, 50)),
            # different ward
            (user_with_name, self.person_b, self.ward_b, date(2020, 4, 24),
                False, False, None, datetime(2020, 3, 1, 10, 50)),
        )
        for (user, person, ward, day, added, continued, until,
             change_time) in data:
            ChangeLogging.objects.create(
                company=self.company,
                user=user, person=person, ward=ward, day=day, added=added,
                continued=continued, until=until, change_time=change_time)

    def test_changehistory_empty(self):
        """ Test 'changehistory' with no data
        """
        response = self.client.get(
            reverse(
                'changehistory', kwargs={'date': '20200424', 'ward_id': '3'}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.content, b'[]')

    def test_changehistory_with_data(self):
        """ Test 'changehistory' with data
        """
        self._apply_changes()
        response = self.client.get(
            reverse('changehistory', kwargs={
                'date': '20200424',
                'ward_id': str(self.ward_a.id)}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, HTTPStatus.OK)

        got = json.loads(response.content)
        self.assertEqual(len(got), 5)
        for res, exp in zip(got, self.expected):
            for key in ('user', 'person', 'ward', 'day', 'added', 'continued',
                        'until'):
                self.assertEqual(res[key], exp[key], msg=str(exp))

    def test_updates(self):
        """ Test if 'updates' return the right data
        """
        self._apply_changes()
        response = self.client.get(
            "/updates/0",
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        res = json.loads(response.content)
        for cl_dict in [
             {'action': 'add', 'continued': True, 'day': '20200401',
              'person': 'A', 'pk': 1, 'ward': 'A'},
             {'action': 'remove', 'continued': True, 'day': '20200410',
              'person': 'A', 'pk': 2, 'ward': 'A'},
             {'action': 'add', 'continued': True, 'day': '20200420',
              'person': 'A', 'pk': 3, 'until': '20200424', 'ward': 'A'},
             {'action': 'add', 'continued': True, 'day': '20200424',
              'person': 'B', 'pk': 4, 'until': '20200430', 'ward': 'A'},
             {'action': 'remove', 'continued': False, 'day': '20200424',
              'person': 'B', 'pk': 5, 'ward': 'A'},
             {'action': 'remove', 'continued': False, 'day': '20200425',
              'person': 'B', 'pk': 6, 'ward': 'A'},
             {'action': 'remove', 'continued': False, 'day': '20200424',
              'person': 'B', 'pk': 7, 'ward': 'B'}]:
            self.assertIn(cl_dict, res['cls'])
        self.assertEqual(len(res['cls']), 7)
        self.assertEqual(
            res['last_change']['pk'],
            ChangeLogging.objects.filter(
                company=self.company).order_by('pk').last().pk)

        response = self.client.get(
            "/updates/5",
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        res = json.loads(response.content)
        for cl_dict in [
             {'action': 'remove', 'continued': False, 'day': '20200425',
              'person': 'B', 'pk': 6, 'ward': 'A'},
             {'action': 'remove', 'continued': False, 'day': '20200424',
              'person': 'B', 'pk': 7, 'ward': 'B'}]:
            self.assertIn(cl_dict, res['cls'])
        self.assertEqual(len(res['cls']), 2)

        response = self.client.get(
            "/updates/7",
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, HTTPStatus.NOT_MODIFIED)


class TestDifferentDays(ViewsTestCase):
    """ Set different planning for a day and ward
    """


class TestChangePassword(ViewsTestCase):

    def test_password_change(self):
        """ Test if 'password_change' answers at all """
        response = self.client.get(reverse('password_change'))
        self.assertEqual(response.status_code, HTTPStatus.OK)


class TestRobotsTxt(TestCase):
    def test_get(self):
        response = self.client.get("/robots.txt")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response["content-type"], "text/plain")
        lines = response.content.decode().splitlines()
        self.assertEqual(lines[0], "User-Agent: *")

    def test_post_disallowed(self):
        response = self.client.post("/robots.txt")

        self.assertEqual(HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
