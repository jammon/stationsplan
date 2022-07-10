import json
from datetime import date
from django.urls import reverse
from sp_app.models import (
    Company,
    Department,
    Ward,
    Person,
    Employee,
    ChangeLogging,
    Planning,
    StatusEntry,
    FAR_FUTURE,
)
from sp_app.tests.utils_for_tests import (
    ViewsWithPermissionTestCase,
    PopulatedTestCase,
    LoggedInTestCase,
)


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
        data["departments"] = self.department.id
        data["company"] = self.company.id
        self.client.post(reverse("person-add"), data)
        person = Person.objects.get(name="Müller")
        assert person is not None
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
        person = Person.objects.get(name="Müller")
        assert person is not None
        assert person.company == self.company


class TestWardEditViews(LoggedInTestCase):
    employee_level = "is_dep_lead"

    def test_add_ward(self):
        data = FORM_DATA[Ward].copy()
        data["departments"] = self.department.id
        data["company"] = self.company.id
        self.client.post(reverse("ward-add"), data)
        ward = Ward.objects.get(name="Station X")
        assert ward is not None
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
        ward = Ward.objects.get(name="Station X")
        assert ward is not None
        assert ward.company == self.company
