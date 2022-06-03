# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from sp_app import forms, business_logic, utils
from .models import Person, Ward, Company, Department, Employee, StatusEntry


def home(request):
    if request.user.is_authenticated:
        return redirect("plan")
    return render(request, "sp_app/index.html", context={"next": "/plan"})


@login_required
def plan(request, month="", day=""):
    """Delivers all the data to built the month-, day- and on-call-view
    on the client side.

    This view is called by 'plan', 'dienste', and 'tag'.

    month is '' or 'YYYYMM'
    day is '' or 'YYYYMMDD' or None (for path "/tag")
    """
    return render(
        request,
        "sp_app/plan.html",
        business_logic.get_plan_data(
            company_id=request.session.get("company_id"),
            department_ids=request.session.get("department_ids"),
            month=month,
            day=day,
            is_editor=request.session.get("is_editor", False),
            is_dep_lead=request.session.get("is_dep_lead", False),
            is_company_admin=request.session.get("is_company_admin", False),
        ),
    )


@login_required
@permission_required("sp_app.is_dep_lead")
def persons_wards(request):
    department_ids = request.session.get("department_ids")
    persons = Person.objects.filter(
        departments__id__in=department_ids
    ).order_by("position", "name")
    wards = Ward.objects.filter(departments__id__in=department_ids).distinct()
    return render(
        request,
        "sp_app/structure/person_ward_list.html",
        {
            "persons": persons,
            "former_persons": any(not p.current() for p in persons),
            "wards": wards,
            "inactive_wards": any(not w.active for w in wards),
            "email_available": settings.EMAIL_AVAILABLE,
        },
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
        if is_company_admin
        else None
    )
    if is_company_admin:
        filter = {"company_id": request.session["company_id"]}
    else:
        filter = {"departments__id__in": request.session["department_ids"]}
    persons = Person.objects.filter(**filter).order_by("position", "name")
    wards = Ward.objects.filter(**filter).distinct()
    return render(
        request,
        "sp_app/setup.html",
        {
            "company": company,
            "is_company_admin": is_company_admin,
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
        "sp_app/ical/ical_feeds.html",
        {"persons": [p for p in persons if p.current()]},
    )


def send_activation_mail(request, user, send=True):
    # can be called with send=False for testing
    if isinstance(user, int):
        user = get_object_or_404(User, pk=user)
    if send:
        utils.send_activation_mail(user)
    return render(
        request, "sp_app/signup/activation_mail_sent.html", {"user": user}
    )


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
            department=None,
            company_id=request.session["company_id"],
        )
        return send_activation_mail(request, user)
    return render(
        request,
        "sp_app/signup/signup.html",
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
        return render(
            request,
            "sp_app/signup/activation_success.html",
            {"next": reverse("persons")},
        )
    return render(request, "sp_app/signup/activation_invalid.html", {})


def test_activation_success(request):
    return render(
        request, "sp_app/signup/activation_success.html", {"next": "/TODO"}
    )
