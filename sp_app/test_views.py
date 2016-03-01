# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from datetime import date
from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Permission
import json

from .utils import PopulatedTestCase
from .models import Employee, Person, ChangeLogging


class TestViewsAnonymously(TestCase):

    def test_view_redirects_to_login(self):
        c = Client()
        for url in ('change', 'plan'):
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
        self.assertEqual(c.post('/change/', {}).status_code, 404)


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
        self.person_a = Person.objects.create(
            name="Person A", shortname="A", company=self.company)
        self.person_b = Person.objects.create(
            name="Person B", shortname="B", company=self.company)
        self.person_a.departments.add(self.department)
        self.person_b.departments.add(self.department)
        self.person_a.functions.add(self.ward_a, self.ward_b)
        self.person_b.functions.add(self.ward_a, self.ward_b)

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
            'user: Person A ist ab 20.01.2016 für Ward A eingeteilt')
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
            'user: Person B ist ab 20.01.2016 nicht mehr für Ward A eingeteilt')
        self.assertEqual(
            json.loads(cl.json),
            {"action": "remove", "person": "B", "ward": "A", "day": "20160120",
             "continued": False})
        self.assertEqual(cl.version, 1)
