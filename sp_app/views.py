# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from sp_app import forms, logic, utils
from .models import (
    Person,
    Ward,
    Company,
    Department,
    Employee,
    StatusEntry,
    Planning,
    ChangeLogging,
    EMPLOYEE_LEVEL,
)


def home(request):
    if request.user.is_authenticated:
        return redirect("plan")
    return render(request, "sp_app/index.jinja", context={"next": "/plan"})


@login_required
def plan(request, month="", day=""):
    """Delivers all the data to built the month-, day- and on-call-view
    on the client side.

    This view is called by 'plan', 'dienste', and 'tag'.

    month is '' or 'YYYYMM'
    day is '' or 'YYYYMMDD' or None (for path "/tag")
    """
    data = logic.get_plan_data(
        company_id=request.session.get("company_id"),
        department_ids=request.session.get("department_ids"),
        month=month,
        day=day,
        is_editor=request.session.get("is_editor", False),
        is_dep_lead=request.session.get("is_dep_lead", False),
        is_company_admin=request.session.get("is_company_admin", False),
    )
    if data is None:
        return redirect("setup")
    return render(
        request,
        "sp_app/plan.jinja",
        data,
    )


@login_required
@permission_required("sp_app.is_dep_lead")
def setup(request):
    """Show settings of the company

    TODO: optimize SQL queries on user/group permissions
    """
    is_company_admin = request.session.get("is_company_admin", False)
    company = (
        Company.objects.select_related("region")
        .prefetch_related("departments", "employees__user")
        .get(id=request.session["company_id"])
    )
    if is_company_admin:
        filter = {"company_id": request.session["company_id"]}
    else:
        filter = {"departments__id__in": request.session["department_ids"]}
    persons = Person.objects.filter(**filter).order_by("position", "name")
    wards = Ward.objects.filter(**filter).distinct()
    return render(
        request,
        "sp_app/setup.jinja",
        {
            "company": company,
            "is_company_admin": is_company_admin,
            "employees": company.employees.all(),
            "persons": persons,
            "former_persons": any(not p.current() for p in persons),
            "wards": wards,
            "inactive_wards": any(not w.active for w in wards),
            "email_available": settings.EMAIL_AVAILABLE,
        },
    )


@login_required
@permission_required("sp_app.is_dep_lead")
def ical_feeds(request):
    """List and edit the ical feeds of all persons of these departments"""
    department_ids = request.session.get("department_ids")
    persons = Person.objects.filter(
        departments__id__in=department_ids
    ).order_by("position", "name")
    return render(
        request,
        "sp_app/ical/ical_feeds.jinja",
        {"persons": [p for p in persons if p.current()]},
    )


def send_activation_mail(request, user):
    if isinstance(user, int):
        user = get_object_or_404(User, pk=user)
    logic.send_activation_mail(user)
    request.session["mail_sent_to"] = user.email
    request.session["mail_sent_to_pk"] = user.pk
    return redirect("signup-success")


def signup(request):
    userform = forms.UserSignupForm(request.POST or None)
    companyform = forms.CompanyForm(request.POST or None)
    departmentform = forms.DepartmentSignupForm(request.POST or None)
    if (
        userform.is_valid()
        and companyform.is_valid()
        and departmentform.is_valid()
    ):
        user = userform.save(commit=False)
        # Users have to be activated, except for playwright tests
        if user.username != "_pwt_user":
            user.is_active = False
        user.save()
        company = companyform.save()
        department = Department.objects.create(
            name=departmentform.cleaned_data["department"], company=company
        )
        employee = Employee.objects.create(user=user, company=company)
        employee.departments.add(department)
        employee.set_level("is_company_admin")
        StatusEntry.objects.create(
            name="New User and Company",
            content=f"{user.username} hat {company.name} erstellt",
            department=department,
            company=company,
        )
        return send_activation_mail(request, user)
    return render(
        request,
        "sp_app/signup/signup.jinja",
        {
            "userform": userform,
            "companyform": companyform,
            "departmentform": departmentform,
        },
    )


def activate(request, uid, token):
    try:
        user = User.objects.get(pk=uid)
    except (ValueError, User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return redirect("activation_success")
    return render(request, "sp_app/signup/activation_invalid.html", {})


def delete_playwright_tests(request):
    if settings.SERVER_TYPE == "production":
        return HttpResponse("Not allowed on production server.")
    n_del, _ = Company.objects.filter(name="_pw_test_company").delete()
    User.objects.filter(username__startswith="_pwt_").delete()
    return render(
        request, "sp_app/delete_playwright_tests.jinja", {"no_deleted": n_del}
    )


def error_for_testing(request):
    assert False


_TEST_COMPANY_NAME = "_pw_test_company2"


def make_test_data(request):
    if settings.SERVER_TYPE == "production":
        return HttpResponse("No Testdata in production")
    if Company.objects.filter(name=_TEST_COMPANY_NAME).exists():
        return HttpResponse("Testdata already exist")
    company = Company.objects.create(
        name=_TEST_COMPANY_NAME, shortname="_pwt_2", region_id=1
    )
    innere = Department.objects.create(
        name="Innere", shortname="Inn", company=company
    )
    chirurgie = Department.objects.create(
        name="Chirurgie", shortname="Chi", company=company
    )
    wards = {}

    for sn in ("A", "B"):
        wards[sn] = Ward.objects.create(
            name=f"Ward {sn}", shortname=sn, max=3, min=2, company=company
        )
        wards[sn].departments.add(innere)
    for sn in ("A", "B"):
        person = Person.objects.create(
            name=f"Person {sn}", shortname=sn, company=company
        )
        person.departments.add(innere)
        person.functions.add(*wards.values())
    chirurg = Person.objects.create(
        name=f"Chirurg", shortname="Chir", company=company
    )
    chirurg.departments.add(chirurgie)

    for level in EMPLOYEE_LEVEL.keys():
        user = User.objects.create(username=f"_pwt2_{level}")
        user.set_password("123456")
        user.save()
        employee = Employee.objects.create(user=user, company=company)
        employee.set_level(level)
        employee.departments.add(innere)
    return HttpResponse("Testdata created")


def delete_test_data(request):
    "Delete data from the playwright tests"
    if settings.SERVER_TYPE == "production":
        return HttpResponse("No Testdata in production")
    query = {"name__startswith": "Test", "company__name": _TEST_COMPANY_NAME}
    Department.objects.filter(**query).delete()
    Person.objects.filter(**query).delete()
    Ward.objects.filter(**query).delete()
    User.objects.filter(username="_Test-Employee").delete()
    Planning.objects.filter(company__name=_TEST_COMPANY_NAME).delete()
    ChangeLogging.objects.filter(company__name=_TEST_COMPANY_NAME).delete()
    return HttpResponse("Data from tests deleted")
