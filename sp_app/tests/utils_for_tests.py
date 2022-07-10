from django.contrib.auth.models import User, Permission
from django.test import TestCase
from sp_app.models import Company, Employee, Person, Ward, Department


class PopulatedTestCase(TestCase):
    """TestCase with some prepared objects."""

    def setUp(self):
        self.company = Company.objects.create(name="Company", shortname="Comp")
        self.department = Department.objects.create(
            name="Department 1", shortname="Dep1", company=self.company
        )
        self.ward_a = Ward.objects.create(
            name="Ward A",
            shortname="A",
            max=3,
            min=2,
            everyday=False,
            on_leave=False,
            company=self.company,
        )
        self.ward_a.departments.add(self.department)
        self.ward_b = Ward.objects.create(
            name="Ward B",
            shortname="B",
            max=2,
            min=1,
            everyday=False,
            on_leave=False,
            company=self.company,
        )
        self.ward_b.departments.add(self.department)
        self.person_a = Person.objects.create(
            name="Person A", shortname="A", company=self.company
        )
        self.person_b = Person.objects.create(
            name="Person B", shortname="B", company=self.company
        )
        self.person_a.departments.add(self.department)
        self.person_b.departments.add(self.department)
        self.person_a.functions.add(self.ward_a, self.ward_b)
        self.person_b.functions.add(self.ward_a, self.ward_b)
        self.user = User.objects.create(username="Mr. User", password="123456")

    def assertContainsDict(self, given, expected):
        for key, value in expected.items():
            self.assertEqual(
                given[key],
                value,
                f"{{ {repr(key)}: {repr(given[key])}, ...}} != "
                f"{{ {repr(key)}: {repr(value)}, ...}}",
            )


class LoggedInTestCase(PopulatedTestCase):
    """PopulatedTestCase with user logged in"""

    employee_level = None

    def setUp(self):
        super(LoggedInTestCase, self).setUp()
        self.user = User.objects.create_user(
            "user", "user@domain.tld", "password"
        )
        self.employee = Employee.objects.create(
            user=self.user, company=self.company
        )
        self.employee.set_level(self.employee_level)
        self.employee.departments.add(self.department)
        self.client.login(username="user", password="password")


class ViewsTestCase(LoggedInTestCase):
    def setUp(self):
        super().setUp()
        self.DATA_FOR_CHANGE = {
            "day": "20160120",
            "ward_id": self.ward_a.id,
            "continued": False,
            "persons": [
                {"id": self.person_a.id, "action": "add"},
                {"id": self.person_b.id, "action": "remove"},
            ],
            "last_pk": 0,
        }


class ViewsWithPermissionTestCase(ViewsTestCase):
    def setUp(self):
        super().setUp()
        self.user.user_permissions.add(
            Permission.objects.get(codename="is_editor")
        )
        self.user = User.objects.get(pk=self.user.pk)  # -> permission cache
