import json
from datetime import date
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
import pytest
from sp_app.models import (
    Company,
    Department,
    Ward,
    Person,
    Employee,
    DifferentDay,
    StatusEntry,
    FAR_FUTURE,
)
from sp_app.tests.utils_for_tests import (
    PopulatedTestCase,
    ViewsWithPermissionTestCase,
    LoggedInTestCase,
)
from sp_app import ajax


class TestChangeApproval(ViewsWithPermissionTestCase):
    def test_change_approved(self):
        """Test if post 'set_approved' sets approvals"""
        self.client.post(
            reverse("set_approved"),
            json.dumps({"wards": ["A", "B"], "date": "20170414"}),
            "text/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        stat = StatusEntry.objects.order_by("-pk").first()
        self.assertEqual(stat.content, "user: A, B ist bis 20170414 sichtbar")
        for ward_id in "AB":
            ward = Ward.objects.get(shortname=ward_id)
            self.assertEqual(ward.approved, date(2017, 4, 14))

        self.client.post(
            reverse("set_approved"),
            json.dumps({"wards": ["A"], "date": False}),
            "text/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        stat = StatusEntry.objects.order_by("-pk").first()
        self.assertEqual(stat.content, "user: A ist unbegrenzt sichtbar")
        ward = Ward.objects.get(shortname="A")
        self.assertEqual(ward.approved, FAR_FUTURE)
        ward = Ward.objects.get(shortname="B")
        self.assertEqual(ward.approved, date(2017, 4, 14))


FORM_DATA = {
    Person: {
        "name": "Müller",
        "shortname": "Mül",
        "start_date": "2022-05-01",
        "end_date": "2099-12-31",
        "position": str(Person.POSITION_ASSISTENTEN),
        "email": "m.mueller@example.com",
        "company": "1",
    },
    Ward: {
        "name": "Station X",
        "shortname": "X",
        "max": 3,
        "min": 1,
        "position": 1,
        "company": "1",
    },
}
PERSON_WARD_FIXTURE = {
    Person: {
        "query": {"name": "Müller"},
        "url": reverse("person-add"),
    },
    Ward: {
        "query": {"name": "Station X"},
        "url": reverse("ward-add"),
    },
}


class TestPermissions_NoPermission(LoggedInTestCase):
    """Test if permissions are respected"""

    matrix = {
        (Person, "department"): "forbidden",
        (Person, "other_dept"): "forbidden",
        (Ward, "department"): "forbidden",
        (Ward, "other_dept"): "forbidden",
    }

    def setUp(self):
        super().setUp()
        self.other_comp = Company.objects.create(name="Other", shortname="Oth")
        self.other_dept = Department.objects.create(
            name="Other", company=self.company
        )

    def get_post_data(self, model, department_id, company_id):
        data = FORM_DATA[model].copy()
        data["departments"] = str(department_id)
        return data

    def check_post_successful(self, response, model):
        """Return True is post was successful"""
        try:
            obj = model.objects.get(**PERSON_WARD_FIXTURE[model]["query"])
            print(model.__name__, obj.name)
            obj.delete()
            return response.status_code == 200
        except model.DoesNotExist:
            return False

    def check_post_unsuccessful(self, response, model):
        """Return True is post was allowed but unsuccessful"""
        return (
            response.status_code == 200
            and not model.objects.filter(
                **PERSON_WARD_FIXTURE[model]["query"]
            ).exists()
        )

    def check_post_forbidden(self, response, model):
        """Return True is post was forbidden"""
        return response.status_code == 403

    def test_post(self):
        for key, expectation in self.matrix.items():
            model, dept = key
            data = self.get_post_data(
                model, getattr(self, dept).id, self.company.id
            )
            response = self.client.post(
                PERSON_WARD_FIXTURE[model]["url"], data
            )
            assertion = getattr(self, f"check_post_{expectation}")
            assert assertion(
                response, model
            ), f"{model.__name__} {dept} {self.employee_level}: {expectation}"


class TestPermissions_Editor(TestPermissions_NoPermission):
    employee_level = "is_editor"


class TestPermissions_DepLead(TestPermissions_NoPermission):
    """
    A dep_lead can create Persons and Wards for the own department, but not for other ones

    TODO: The exclusion of Persons/Wards for different departments
    This should not happen using the ui and maybe is not a security problem
    """

    employee_level = "is_dep_lead"
    matrix = {
        (Person, "department"): "successful",
        # (Person, "other_dept"): "unsuccessful",
        (Ward, "department"): "successful",
        # (Ward, "other_dept"): "unsuccessful",
    }


class TestPermissions_CompanyAdmin(TestPermissions_NoPermission):
    employee_level = "is_company_admin"
    matrix = {
        (Person, "department"): "successful",
        (Person, "other_dept"): "successful",
        (Ward, "department"): "successful",
        (Ward, "other_dept"): "successful",
    }


class TestPersonEditViews(LoggedInTestCase):
    employee_level = "is_dep_lead"

    def test_add_person(self):
        data = FORM_DATA[Person].copy()
        data.update(
            {"departments": self.department.id, "company": self.company.id}
        )
        self.client.post(reverse("person-add"), data)
        try:
            person = Person.objects.get(name="Müller")
        except Person.DoesNotExist:
            assert False, "Person was not created"
        for attribute in ("name", "shortname", "email"):
            assert getattr(person, attribute) == data[attribute]
        assert person.start_date == date(2022, 5, 1)
        assert person.end_date == date(2099, 12, 31)
        assert person.company == self.company
        depts = list(person.departments.all())
        assert len(depts) == 1
        assert depts[0] == self.department

        # edit this person
        data = FORM_DATA[Person].copy()
        data.update(
            {
                "departments": self.department.id,
                "company": self.company.id,
                "name": "Müller2",
            }
        )
        self.client.post(reverse("person-update", args=[person.id]), data)
        try:
            person = Person.objects.get(name="Müller2")
        except Person.DoesNotExist:
            assert False, "Person was not changed"
        for attribute in ("name", "shortname", "email"):
            assert getattr(person, attribute) == data[attribute]
        assert person.start_date == date(2022, 5, 1)
        assert person.end_date == date(2099, 12, 31)
        assert person.company == self.company
        depts = list(person.departments.all())
        assert len(depts) == 1
        assert depts[0] == self.department

    def test_wrong_company(self):
        """Protect from users forging data for other companies"""
        data = FORM_DATA[Person].copy()
        data["departments"] = self.department.id
        data["company"] = Company.objects.create(
            name="Other", shortname="Oth"
        ).id
        self.client.post(reverse("person-add"), data)
        try:
            person = Person.objects.get(name="Müller")
        except Person.DoesNotExist:
            assert False, "Person was not created"
        assert person.company == self.company


class TestWardEditViews(LoggedInTestCase):
    employee_level = "is_dep_lead"

    def test_add_ward(self):
        data = FORM_DATA[Ward].copy()
        data.update(
            {"departments": self.department.id, "company": self.company.id}
        )
        self.client.post(reverse("ward-add"), data)
        try:
            ward = Ward.objects.get(name="Station X")
        except Ward.DoesNotExist:
            assert False, "Ward was not created"
        for attribute in ("name", "shortname", "max", "min", "position"):
            assert getattr(ward, attribute) == data[attribute]
        assert ward.company == self.company
        depts = list(ward.departments.all())
        assert len(depts) == 1
        assert depts[0] == self.department

        # edit this ward
        data = FORM_DATA[Ward].copy()
        data.update(
            {
                "departments": self.department.id,
                "company": self.company.id,
                "name": "Station Y",
            }
        )
        self.client.post(reverse("ward-update", args=[ward.id]), data)
        try:
            ward = Ward.objects.get(name="Station Y")
        except Ward.DoesNotExist:
            assert False, "Ward was not created"
        for attribute in ("name", "shortname", "max", "min", "position"):
            assert getattr(ward, attribute) == data[attribute]
        assert ward.company == self.company
        depts = list(ward.departments.all())
        assert len(depts) == 1
        assert depts[0] == self.department

    def test_wrong_company(self):
        """Protect from users forging data for other companies"""
        data = FORM_DATA[Ward].copy()
        data["departments"] = self.department.id
        data["company"] = Company.objects.create(
            name="Other", shortname="Oth"
        ).id
        self.client.post(reverse("ward-add"), data)
        try:
            ward = Ward.objects.get(name="Station X")
        except Ward.DoesNotExist:
            assert False, "Ward was not created"
        assert ward.company == self.company


class TestDepartmentEditViews(LoggedInTestCase):
    employee_level = "is_company_admin"

    def test_add_department(self):
        data = {
            "name": "New department",
            "shortname": "New",
            "company": self.company.id,
        }
        response = self.client.post(reverse("department-add"), data)
        try:
            department = Department.objects.get(name="New department")
        except Department.DoesNotExist:
            assert False, "Department was not created"
        for attribute in ("name", "shortname"):
            assert getattr(department, attribute) == data[attribute]
        assert department.company == self.company

        assert "New department" in str(response.content)

    def test_wrong_company(self):
        """Protect from users forging data for other companies"""
        data = {
            "name": "New department",
            "shortname": "New",
        }
        data["company"] = Company.objects.create(
            name="Other", shortname="Oth"
        ).id
        self.client.post(reverse("department-add"), data)
        try:
            department = Department.objects.get(name="New department")
        except Department.DoesNotExist:
            assert False, "Department was not created"
        assert department.company == self.company


class TestEmployeeEditViews:
    @pytest.fixture
    def employee_level(self):
        return "is_company_admin"

    @pytest.fixture(autouse=True)
    def enable_db_access_for_all_tests(self, db):
        pass

    def test_delete_employee(self, logged_in, other_employee, client):
        response = client.get(
            reverse("employee-delete", args=(other_employee.id,))
        )
        msg = "other_employee kann sich nicht mehr als Bearbeiter/in anmelden"
        assert msg in str(response.content)
        user = User.objects.get(id=other_employee.user.id)
        assert not user.is_active

    def test_delete_current(self, logged_in, client, employee):
        response = client.get(reverse("employee-delete", args=(employee.id,)))
        msg = "Aktive/r Bearbeiter/in kann nicht deaktiviert werden"
        assert msg in str(response.content)
        user = User.objects.get(id=employee.user.id)
        assert user.is_active

    def test_delete_not_existing(self, logged_in, client):
        response = client.get(reverse("employee-delete", args=(999999,)))
        msg = "Bearbeiter/in nicht gefunden"
        assert msg in str(response.content)


class TestChangeFunction(LoggedInTestCase):
    employee_level = "is_dep_lead"

    def testChangeFunction(self):
        def functions():
            return set(f.shortname for f in self.person_a.functions.all())

        assert functions() == set(("A", "B"))
        data = {
            "person": self.person_a.id,
            "ward": self.ward_a.id,
            "add": False,
        }
        url = reverse("change_function")
        response = self.client.post(
            url, json.dumps(data), content_type="application/json"
        )
        assert functions() == set("B")
        assert json.loads(response.content) == {
            "status": "ok",
            "person": "A",
            "functions": ["B"],
        }
        data["add"] = True
        response = self.client.post(
            url, json.dumps(data), content_type="application/json"
        )
        assert functions() == set(("A", "B"))
        assert json.loads(response.content) == {
            "status": "ok",
            "person": "A",
            "functions": ["A", "B"],
        }

        wrong = data.copy()
        wrong["person"] = 777
        response = self.client.post(
            url, json.dumps(wrong), content_type="application/json"
        )
        assert json.loads(response.content) == {
            "status": "error",
            "reason": "Person 777 not found",
        }

        wrong = data.copy()
        wrong["ward"] = 777
        response = self.client.post(
            url, json.dumps(wrong), content_type="application/json"
        )
        assert json.loads(response.content) == {
            "status": "error",
            "reason": "Ward 777 not found",
        }


class TestDifferentday(LoggedInTestCase):
    employee_level = "is_dep_lead"

    def test_differentday(self):
        # set different day
        data = {
            "action": "add_additional",
            "ward": self.ward_a.id,
            "day_id": "20220710",
        }
        response = self.client.post(reverse("different-day", kwargs=data))
        assert json.loads(response.content) == {"status": "ok"}
        dd = DifferentDay.objects.get(day=date(2022, 7, 10))
        assert dd.added
        assert dd.ward == self.ward_a
        # once again
        response = self.client.post(reverse("different-day", kwargs=data))
        assert json.loads(response.content) == {
            "status": "error",
            "message": "There is a different planning already",
        }
        # remove it
        data["action"] = "remove_additional"
        response = self.client.post(reverse("different-day", kwargs=data))
        assert json.loads(response.content) == {"status": "ok"}
        assert not DifferentDay.objects.filter(day=date(2022, 7, 10)).exists()
        # once again
        response = self.client.post(reverse("different-day", kwargs=data))
        assert json.loads(response.content) == {
            "status": "error",
            "message": "There is no different planning for this day",
        }


class TestDepartment2(PopulatedTestCase):
    class Request:
        def __init__(self, session):
            self.session = session

    def setUp(self):
        super().setUp()
        self.dep2 = Department.objects.create(
            name="Department 2", shortname="Dep2", company=self.company
        )


class TestPersonsForRequest_Admin(TestDepartment2):
    def setUp(self):
        super().setUp()
        self.person_2a = Person.objects.create(
            name="Person 2A", shortname="2A", company=self.company
        )
        self.person_2a.departments.add(self.dep2)

    def test_admin(self):
        request = self.Request(
            {
                "company_id": self.company.id,
                "department_ids": [self.department.id],
                "is_company_admin": True,
            }
        )
        persons = list(ajax.persons_for_request(request))
        for p in (self.person_a, self.person_b, self.person_2a):
            assert p in persons

    def test_not_admin(self):
        request = self.Request(
            {
                "company_id": self.company.id,
                "department_ids": [self.department.id],
                "is_company_admin": False,
            }
        )
        persons = list(ajax.persons_for_request(request))
        for p in (self.person_a, self.person_b):
            assert p in persons
        assert self.person_2a not in persons


class TestWardsForRequest(TestDepartment2):
    def setUp(self):
        super().setUp()
        self.ward_2a = Ward.objects.create(
            name="Ward 2A", shortname="2A", max=3, min=2, company=self.company
        )
        self.ward_2a.departments.add(self.dep2)

    def test_admin(self):
        request = self.Request(
            {
                "company_id": self.company.id,
                "department_ids": [self.department.id],
                "is_company_admin": True,
            }
        )
        wards = list(ajax.wards_for_request(request))
        for w in (self.ward_a, self.ward_b, self.ward_2a):
            assert w in wards

    def test_not_admin(self):
        request = self.Request(
            {
                "company_id": self.company.id,
                "department_ids": [self.department.id],
                "is_company_admin": False,
            }
        )
        wards = list(ajax.wards_for_request(request))
        for w in (self.ward_a, self.ward_b):
            assert w in wards
        assert self.ward_2a not in wards
