import pytest
import logging
from django.contrib.auth.models import User
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


@pytest.fixture(autouse=True)
def disable_logging():
    """Disable logging in all tests."""
    logging.disable(logging.CRITICAL)


# `db` is a pytest fixture that ensures that the Django database is set up
@pytest.fixture
def company(db):
    return Company.objects.create(name="Company", shortname="Comp")


@pytest.fixture
def department(company):
    return Department.objects.create(
        name="Department 1", shortname="Dep1", company=company
    )


@pytest.fixture
def ward_a(company, department):
    ward_a = Ward.objects.create(
        name="Ward A", shortname="A", max=3, min=2, company=company
    )
    ward_a.departments.add(department)
    return ward_a


@pytest.fixture
def ward_b(company, department):
    ward_b = Ward.objects.create(
        name="Ward B", shortname="B", max=2, min=2, company=company
    )
    ward_b.departments.add(department)
    return ward_b


@pytest.fixture
def person_a(company, department):
    person_a = Person.objects.create(
        name="Person A", shortname="A", company=company
    )
    person_a.departments.add(department)
    return person_a


@pytest.fixture
def person_b(company, department):
    person_b = Person.objects.create(
        name="Person B", shortname="B", company=company
    )
    person_b.departments.add(department)
    return person_b


@pytest.fixture
def user():
    return User.objects.create_user("user", "user@domain.tld", "password")


@pytest.fixture
def employee(user, company, department, employee_level):
    employee = Employee(user=user, company=company)
    employee.set_level(employee_level)
    employee.departments.add(department)
    return employee


@pytest.fixture
def logged_in(client, employee, user):
    client.login(username="user", password="password")


@pytest.fixture
def user_mueller():
    return User.objects.create_user(
        "hmueller",
        "user@domain.tld",
        "password",
        first_name="Heinz",
        last_name="Müller",
    )


@pytest.fixture
def employee_mueller(user_mueller, company, department):
    employee = Employee.objects.create(user=user_mueller, company=company)
    employee.departments.add(department)
    return employee


@pytest.fixture
def other_user():
    return User.objects.create_user(
        "other_employee", "other_employee@domain.tld", "password"
    )


@pytest.fixture
def other_employee(other_user, company):
    return Employee.objects.create(user=other_user, company=company)


@pytest.fixture
def logged_in(user, employee, client):
    client.force_login(user)
