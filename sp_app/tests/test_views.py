# -*- coding: utf-8 -*-
from datetime import date, datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from http import HTTPStatus
from unittest.mock import Mock
import json
import logging
import pytest

from requests import request

from sp_app.models import (
    Company,
    Department,
    Ward,
    Person,
    Employee,
    ChangeLogging,
    Planning,
)
from sp_app import logic, ajax
from sp_app.logic import get_plan_data
from sp_app.tests.utils_for_tests import (
    PopulatedTestCase,
    LoggedInTestCase,
    ViewsTestCase,
    ViewsWithPermissionTestCase,
)


class TestViewsAnonymously(TestCase):
    def test_view_redirects_to_login(self):
        """Test if 'plan', 'functions' and 'password_change' redirect
        to login if not logged in
        """
        c = Client()
        for name, url in (
            ("plan", "/plan/"),
            ("functions", "/zuordnung"),
            ("password_change", "password_change/"),
        ):
            response = c.get(reverse(name))
            self.assertEqual(response.status_code, HTTPStatus.FOUND, msg=name)
            # TODO: why does this fail for 'password_change'?
            if name != "password_change":
                for mode, f in (("get", c.get), ("post", c.post)):
                    response = f(reverse(name), follow=True)
                    self.assertRedirects(
                        response,
                        "/login/?next=" + url,
                        msg_prefix=f"{mode} - {url}",
                    )

    def test_changes(self):
        """Test if 'changes' return status HTTPStatus.FORBIDDEN if not logged in"""
        c = Client()
        response = c.get(reverse("changes"), {})
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        response = c.post(reverse("changes"), {})
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)


class TestPlanData(PopulatedTestCase):
    """Test business logic for views.plan"""

    def test_get_plan_data(self):
        given = (
            (date(2016, 1, 1), date(2016, 1, 31)),  # older than 1 mon
            (date(2016, 2, 1), date(2016, 3, 1)),  # less than 1 mon
            (date(2016, 1, 1), date(2016, 4, 15)),
            (date(2016, 1, 1), date(2016, 5, 31)),
            (date(2016, 4, 1), date(2016, 4, 30)),
            (date(2016, 4, 1), date(2016, 5, 31)),
            (date(2016, 5, 1), date(2016, 5, 31)),
        )
        expected_list = (
            {"start": "20160201", "end": "20160301"},
            {"start": "20160101", "end": "20160415"},
            {"start": "20160101", "end": "20160531"},
            {"start": "20160401", "end": "20160430"},
            {"start": "20160401", "end": "20160531"},
            {"start": "20160501", "end": "20160531"},
        )
        for start, end in given:
            Planning.objects.create(
                company=self.company,
                person=self.person_a,
                ward=self.ward_a,
                start=start,
                end=end,
            )
        plan_data = get_plan_data(
            department_ids=[self.department.id],
            company_id=self.company.id,
            month="201604",
        )
        data = json.loads(plan_data["data"])
        for value, expected in zip(data["plannings"], expected_list):
            self.assertEqual(value["person"], self.person_a.id)
            self.assertEqual(value["ward"], self.ward_a.id)
            self.assertEqual(value["start"], expected["start"])
            self.assertEqual(value["end"], expected["end"])

    def test_inactive_ward(self):
        for ward in (self.ward_a, self.ward_b):
            Planning.objects.create(
                company=self.company,
                person=self.person_a,
                ward=ward,
                start=date(2016, 4, 1),
                end=date(2016, 4, 10),
            )
        Ward.objects.filter(shortname="B").update(active=False)

        plan_data = get_plan_data(
            department_ids=[self.department.id],
            company_id=self.company.id,
            month="201604",
        )
        data = json.loads(plan_data["data"])
        plannings = data["plannings"]
        self.assertEqual(len(plannings), 1)
        self.assertEqual(plannings[0]["ward"], self.ward_a.id)

    def test_persons_and_wards(self):
        """Persons and Wards are included in the data
        but not from other Companies, former persons or inactive wards
        """
        other_comp = Company.objects.create(
            name="OtherComp",
            shortname="Oth",
        )
        other_person = Person.objects.create(
            name="OtherComp", shortname="Oth", company=other_comp
        )
        former = Person.objects.create(
            name="Former",
            shortname="For",
            company=self.company,
            end_date=date(2021, 12, 31),
        )
        other_ward = Ward.objects.create(
            name="OtherComp",
            shortname="Oth",
            max=0,
            min=3,
            company=other_comp,
        )
        inactive_ward = Ward.objects.create(
            name="Inactive",
            shortname="Ina",
            max=0,
            min=3,
            company=self.company,
            active=False,
        )
        inactive_ward.departments.add(self.department)

        assert self.department.name == "Department 1"
        assert list(inactive_ward.departments.all()) == [self.department]

        plan_data = get_plan_data(
            department_ids=[self.department.id],
            company_id=self.company.id,
            month="202205",
        )
        data = json.loads(plan_data["data"])
        person_ids = [p["id"] for p in data["persons"]]
        assert self.person_a.id in person_ids
        assert self.person_b.id in person_ids
        assert other_person not in person_ids
        assert former not in person_ids
        assert former in plan_data["former_persons"]

        ward_ids = [w["id"] for w in data["wards"]]
        assert self.ward_a.id in ward_ids
        assert self.ward_b.id in ward_ids
        assert other_ward.id not in ward_ids
        assert inactive_ward.id not in ward_ids
        assert inactive_ward in plan_data["inactive_wards"]


class TestPlan(ViewsTestCase):
    """Test views.plan"""

    def test_plan(self):
        response = self.client.get("/plan/201604")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_other_entries(self):
        response = self.client.get("/dienste/201604")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.client.get("/tag/201604")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.client.get("/zuordnung")
        self.assertEqual(response.status_code, HTTPStatus.OK)


# Tests for sp_app.ajax


class TestChangeForbidden(ViewsTestCase):
    """User without permission to add changes"""

    def do_test(self, view, data):
        # Disable logging of "PermissionDenied",
        # so not to clutter debug.log
        logging.disable(logging.CRITICAL)
        response = self.client.post(
            reverse(view),
            data,
            "text/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        logging.disable(logging.NOTSET)

    def test_changes(self):
        """Test if 'changes' return status HTTPStatus.FORBIDDEN if not logged in"""
        self.do_test("changes", json.dumps(self.DATA_FOR_CHANGE))

    def test_approval(self):
        """Test if 'set_approved' return status HTTPStatus.FORBIDDEN if not logged in"""
        self.do_test("set_approved", "data")


class TestChangeMore(ViewsWithPermissionTestCase):
    def test_with_valid_data(self):
        """Test if post 'changes' creates the right ChangeLoggings and returns them"""
        self.client.post(
            reverse("changes"),
            json.dumps(self.DATA_FOR_CHANGE),
            "text/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        cls = ChangeLogging.objects.all().order_by("person__shortname")
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
            "user: Person A ist am 20.01.2016 für Ward A eingeteilt",
        )
        self.assertContainsDict(
            json.loads(cl.json),
            {
                "action": "add",
                "person": self.person_a.shortname,
                "ward": self.ward_a.shortname,
                "day": "20160120",
                "continued": False,
            },
        )
        self.assertEqual(cl.version, 1)
        cl = cls[1]
        self.assertEqual(cl.person, self.person_b)
        self.assertEqual(cl.ward, self.ward_a)
        self.assertEqual(cl.day, date(2016, 1, 20))
        self.assertEqual(cl.added, False)
        self.assertEqual(cl.continued, False)
        self.assertEqual(
            cl.description,
            "user: Person B ist am 20.01.2016 nicht mehr für Ward A "
            "eingeteilt",
        )
        self.assertContainsDict(
            json.loads(cl.json),
            {
                "action": "remove",
                "person": self.person_b.shortname,
                "ward": self.ward_a.shortname,
                "day": "20160120",
                "continued": False,
            },
        )
        self.assertEqual(cl.version, 1)


@pytest.fixture
def some_changes(
    company, user, user_mueller, person_a, person_b, ward_a, ward_b
):
    def make_cl(
        user=user,
        person=person_a,
        ward=ward_a,
        day=None,
        added=True,
        continued=False,
        until=None,
        change_time=None,
    ):
        ChangeLogging.objects.create(
            company=company,
            user=user,
            person=person,
            ward=ward,
            day=day,
            added=added,
            continued=continued,
            until=until,
            change_time=change_time,
        )

    # ongoing assignment
    make_cl(
        day=date(2020, 4, 1),
        continued=True,
        change_time=datetime(2020, 3, 1, 10),
    )
    # stop it
    make_cl(
        day=date(2020, 4, 10),
        added=False,
        continued=True,
        change_time=datetime(2020, 3, 1, 10, 10),
    )
    # just some time until today
    make_cl(
        day=date(2020, 4, 20),
        continued=True,
        until=date(2020, 4, 24),
        change_time=datetime(2020, 3, 1, 10, 20),
    )
    # just some time from today
    make_cl(
        user=user_mueller,
        person=person_b,
        day=date(2020, 4, 24),
        continued=True,
        until=date(2020, 4, 30),
        change_time=datetime(2020, 3, 1, 10, 30),
    )
    # but not today
    make_cl(
        user=user_mueller,
        person=person_b,
        day=date(2020, 4, 24),
        added=False,
        change_time=datetime(2020, 3, 1, 10, 40),
    )
    # different day
    make_cl(
        user=user_mueller,
        person=person_b,
        day=date(2020, 4, 25),
        added=False,
        change_time=datetime(2020, 3, 1, 10, 50),
    )
    # different ward
    make_cl(
        user=user_mueller,
        person=person_b,
        ward=ward_b,
        day=date(2020, 4, 24),
        added=False,
        change_time=datetime(2020, 3, 1, 10, 50),
    )


class TestGetChangeHistory:
    """Get the change history for a day and ward"""

    expected = [
        {
            "user": "Heinz Müller",
            "person": "B",
            "ward": "A",
            "day": date(2020, 4, 24),
            "added": False,
            "continued": False,
            "until": None,
        },
        {
            "user": "Heinz Müller",
            "person": "B",
            "ward": "A",
            "day": date(2020, 4, 24),
            "added": True,
            "continued": True,
            "until": date(2020, 4, 30),
        },
        {
            "user": "user",
            "person": "A",
            "ward": "A",
            "day": date(2020, 4, 20),
            "added": True,
            "continued": True,
            "until": date(2020, 4, 24),
        },
        {
            "user": "user",
            "person": "A",
            "ward": "A",
            "day": date(2020, 4, 10),
            "added": False,
            "continued": True,
            "until": None,
        },
        {
            "user": "user",
            "person": "A",
            "ward": "A",
            "day": date(2020, 4, 1),
            "added": True,
            "continued": True,
            "until": None,
        },
    ]

    def test_getchangehistory_empty(self, company, ward_a):
        """Test 'ajax._get_change_history' with no data"""
        data = ajax._get_change_history(company.id, "20200424", str(ward_a.id))
        assert data == []

    def test_getchangehistory_with_data(self, company, ward_a, some_changes):
        """Test 'ajax._get_change_history' with data"""
        data = ajax._get_change_history(company.id, "20200424", str(ward_a.id))

        assert len(data) == 5
        for res, exp in zip(data, self.expected):
            for key in (
                "user",
                "person",
                "ward",
                "day",
                "added",
                "continued",
                "until",
            ):
                assert res[key] == exp[key]

    def test_updates(self, company, some_changes):
        """Test if 'updates' return the right data

        Test changed: the data com from logic.get_last_change_response.
        This is tested directly.
        """
        response = logic.get_last_change_response(
            company_id=company.id, last_change_pk=0
        )
        res = json.loads(response.content)
        cls = res["cls"]
        for cl in cls:
            del cl["pk"]
        for cl_dict in [
            {
                "action": "add",
                "continued": True,
                "day": "20200401",
                "person": "A",
                "ward": "A",
            },
            {
                "action": "remove",
                "continued": True,
                "day": "20200410",
                "person": "A",
                "ward": "A",
            },
            {
                "action": "add",
                "continued": True,
                "day": "20200420",
                "person": "A",
                "until": "20200424",
                "ward": "A",
            },
            {
                "action": "add",
                "continued": True,
                "day": "20200424",
                "person": "B",
                "until": "20200430",
                "ward": "A",
            },
            {
                "action": "remove",
                "continued": False,
                "day": "20200424",
                "person": "B",
                "ward": "A",
            },
            {
                "action": "remove",
                "continued": False,
                "day": "20200425",
                "person": "B",
                "ward": "A",
            },
            {
                "action": "remove",
                "continued": False,
                "day": "20200424",
                "person": "B",
                "ward": "B",
            },
        ]:
            assert cl_dict in cls
        assert len(cls) == 7
        last_change_pk = (
            ChangeLogging.objects.filter(company=company)
            .order_by("pk")
            .last()
            .pk
        )
        assert res["last_change"]["pk"] == last_change_pk

        response = logic.get_last_change_response(
            company_id=company.id, last_change_pk=last_change_pk - 2
        )
        res = json.loads(response.content)
        cls = res["cls"]
        for cl in cls:
            del cl["pk"]

        for cl_dict in [
            {
                "action": "remove",
                "continued": False,
                "day": "20200425",
                "person": "B",
                "ward": "A",
            },
            {
                "action": "remove",
                "continued": False,
                "day": "20200424",
                "person": "B",
                "ward": "B",
            },
        ]:
            assert cl_dict in cls
        assert len(cls) == 2

        # TODO
        # response = self.client.get(
        #     "/updates/7", HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        # )
        # self.assertEqual(response.status_code, HTTPStatus.NOT_MODIFIED)


class TestDifferentDays(ViewsTestCase):
    """Set different planning for a day and ward"""


class TestChangePassword(ViewsTestCase):
    def test_password_change(self):
        """Test if 'password_change' answers at all"""
        response = self.client.get(reverse("password_change"))
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


class TestSendActivationMail(PopulatedTestCase):
    def test_send_activation_mail(self):
        logic.send_activation_mail = Mock()
        response = self.client.get(
            reverse("send_activation_mail", args=(self.user.pk,))
        )
        logic.send_activation_mail.assert_called_once()
        (user,) = logic.send_activation_mail.call_args.args
        assert user == self.user
