# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from datetime import date
from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Permission
import json

from .utils import PopulatedTestCase
from .models import Employee, ChangeLogging, Planning


class TestViewsAnonymously(TestCase):

    def test_view_redirects_to_login(self):
        c = Client()
        for url in ('changes', 'plan'):
            response = c.get(reverse(url))
            self.assertEqual(response.status_code, 302, msg=url)
            response = c.get(reverse(url), follow=True)
            self.assertRedirects(response, '/login/?next=%2F'+url,
                                 msg_prefix=url)
            response = c.post(reverse(url), follow=True)
            self.assertRedirects(response, '/login/?next=%2F'+url,
                                 msg_prefix=url)

    def test_status_post(self):
        c = Client()
        response = c.post(reverse('changes'), {})
        self.assertEqual(response.status_code, 302)


class TestPlan(PopulatedTestCase):

    def setUp(self):
        super(TestPlan, self).setUp()
        self.user = User.objects.create_user(
            'user', 'user@domain.tld', 'password')
        self.employee = Employee.objects.create(
            user=self.user, company=self.company)
        self.employee.departments.add(self.department)

    def test_plan(self):
        for start, end in (
                (date(2016, 1, 1), date(2016, 3, 31)),
                (date(2016, 1, 1), date(2016, 4, 15)),
                (date(2016, 1, 1), date(2016, 5, 31)),
                (date(2016, 4, 1), date(2016, 4, 30)),
                (date(2016, 4, 1), date(2016, 5, 31)),
                (date(2016, 5, 1), date(2016, 5, 31)),
                ):
            Planning.objects.create(
                company=self.company, person=self.person_a,
                ward=self.ward_a, start=start, end=end)
        self.client.login(username='user', password='password')
        # response = self.client.get(reverse('plan', kwargs={'month': '201604'}))
        response = self.client.get('/plan/201604')
        self.assertEqual(response.status_code, 200)
        plannings = json.loads(response.context['plannings'])
        for value, expected in zip(plannings, (
                {'start': '20160101', 'end': '20160415'},
                {'start': '20160101', 'end': '20160531'},
                {'start': '20160401', 'end': '20160430'},
                {'start': '20160401', 'end': '20160531'},
                {'start': '20160501', 'end': '20160531'},
                )):
            self.assertEqual(value['person'], 'A')
            self.assertEqual(value['ward'], 'A')
            self.assertEqual(value['start'], expected['start'])
            self.assertEqual(value['end'], expected['end'])


class TestChangeMore(PopulatedTestCase):

    def setUp(self):
        super(TestChangeMore, self).setUp()
        self.user = User.objects.create_user(
            'user', 'user@domain.tld', 'password')
        self.user.user_permissions.add(
            Permission.objects.get(codename='add_changelogging'))
        self.user = User.objects.get(pk=self.user.pk)  # -> permission cache
        self.employee = Employee.objects.create(
            user=self.user, company=self.company)
        self.employee.departments.add(self.department)

    def test_with_valid_data(self):
        data = {'day': '20160120',
                'ward': 'A',
                'continued': False,
                'persons': [
                   {'id': 'A', 'action': 'add', },
                   {'id': 'B', 'action': 'remove', },
                ]}
        self.client.login(username='user', password='password')
        self.client.post(
            reverse('changes'),
            json.dumps(data),
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
        self.assertEqual(
            json.loads(cl.json),
            {"action": "add", "person": "A", "ward": "A", "day": "20160120",
             "continued": False})
        self.assertEqual(cl.version, 1)
        cl = cls[1]
        self.assertEqual(cl.person, self.person_b)
        self.assertEqual(cl.ward, self.ward_a)
        self.assertEqual(cl.day, date(2016, 1, 20))
        self.assertEqual(cl.added, False)
        self.assertEqual(cl.continued, False)
        self.assertEqual(
            cl.description,
            'user: Person B ist am 20.01.2016 nicht mehr für Ward A eingeteilt')
        self.assertEqual(
            json.loads(cl.json),
            {"action": "remove", "person": "B", "ward": "A", "day": "20160120",
             "continued": False})
        self.assertEqual(cl.version, 1)
