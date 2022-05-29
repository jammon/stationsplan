# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from sp_app import forms, business_logic, utils
from .models import Person, Ward, Company, Department, Employee


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
def personen_funktionen(request):
    department_ids = request.session.get("department_ids")
    personen = Person.objects.filter(
        departments__id__in=department_ids
    ).order_by("position", "name")
    funktionen = Ward.objects.filter(
        departments__id__in=department_ids
    ).distinct()
    return render(
        request,
        "sp_app/person_ward_list.html",
        {
            "personen": personen,
            "former_persons": any(not p.current() for p in personen),
            "funktionen": funktionen,
            "inactive_wards": any(not w.active for w in funktionen),
            "email_available": settings.EMAIL_AVAILABLE,
        },
    )


def get_edit_view(
    model_class, formclass, get_initials, redirect_url, template_name
):
    @login_required
    @permission_required("sp_app.is_dep_lead")
    def edit_view(request, pk=None):
        if pk is not None:
            kwargs = {"instance": get_object_or_404(model_class, pk=pk)}
        else:
            kwargs = {"initial": get_initials(request)}
        form = formclass(request.POST or None, **kwargs)
        if form.is_valid():
            form.save()
            return redirect(redirect_url)
        return render(request, template_name, {"form": form})

    return edit_view


def person_initials(request):
    return {
        "company": request.session["company_id"],
        "start_date": utils.get_first_of_month(),
    }


person_edit = get_edit_view(
    Person,
    forms.PersonForm,
    person_initials,
    "/personen",
    "sp_app/person_form.html",
)


def ward_initials(request):
    return {"company": request.session["company_id"]}


ward_edit = get_edit_view(
    Ward,
    forms.WardForm,
    ward_initials,
    "/personen",
    "sp_app/ward_form.html",
)


@login_required
def overview(request):
    """Show settings of the company

    TODO: optimize SQL queries on user/group permissions
    """
    company = (
        Company.objects.select_related("region")
        .prefetch_related("departments", "employees__user")
        .get(id=request.session["company_id"])
    )
    return render(request, "sp_app/overview.html", {"company": company})


@login_required
@permission_required("sp_app.is_dep_lead")
def ical_feeds(request):
    """List and edit the ical feeds of all persons of these departments"""
    department_ids = request.session.get("department_ids")
    personen = Person.objects.filter(
        departments__id__in=department_ids
    ).order_by("position", "name")
    return render(
        request,
        "sp_app/ical_feeds.html",
        {"personen": [p for p in personen if p.current()]},
    )


def send_activation_mail(request, user, send=True):
    # can be called with send=False for testing
    if isinstance(user, int):
        user = get_object_or_404(User, pk=user)
    if send:
        utils.send_activation_mail(user)
    return render(request, "sp_app/activation_mail_sent.html", {"user": user})


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
        return send_activation_mail(request, user)
    return render(
        request,
        "sp_app/signup.html",
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
            "sp_app/activation_success.html",
            {"next": reverse("persons")},
        )
    return render(request, "sp_app/activation_invalid.html", {})


def test_activation_success(request):
    return render(request, "sp_app/activation_success.html", {"next": "/TODO"})
