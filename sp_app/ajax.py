# -*- coding: utf-8 -*-
from datetime import datetime
from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

import json

from .logic import apply_changes, set_approved, get_last_change_response
from .models import (
    ChangeLogging,
    Company,
    Department,
    DifferentDay,
    Employee,
    Person,
    StatusEntry,
    Ward,
    FeedId,
)
from .utils import post_with_company
from sp_app import forms


def ajax_login_required(function=None):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """

    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied
        return function(request, *args, **kwargs)

    return _wrapped_view


@ajax_login_required
@require_POST
@permission_required("sp_app.is_editor", raise_exception=True)
def changes(request):
    """Some *person*s are added to or removed (*action*)
    from the staffing of a *ward*
    on a *day*
    for a *single_day* or for the future
    The data come in this form:
    {'day': <YYYYMMDD>,
     'ward_id': <ward.id>,
     'continued': True|False|<YYYYMMDD>,
     'persons': [{
           'id': <person.id>,
           'action': 'add'|'remove',
         },
         ...
     ],
     'last_pk': <ChangeLogging.pk>}

    Returned are the new changes since 'last_pk',
    including the just transmitted changes, if they succeeded.
    """
    data = json.loads(request.body)
    company_id = request.session["company_id"]
    apply_changes(
        request.user,
        company_id,
        data["day"],
        data["ward_id"],
        data["continued"],
        data["persons"],
    )
    return get_last_change_response(company_id, int(data["last_pk"]))


@ajax_login_required
@require_POST
@permission_required("sp_app.is_editor", raise_exception=True)
def change_approved(request):
    """Set the approved date for a ward.

    The data come in this form:
    {'wards': [<ward.shortname>, ...]
     'date': False|<YYYYMMDD>,
    }
    """
    data = json.loads(request.body)
    res = set_approved(
        data["wards"], data["date"], request.session["department_ids"]
    )
    user_name = request.user.last_name or request.user.get_username()
    wards = ", ".join(res["wards"])
    limit = (f"bis {res['approved']}") if data["date"] else "unbegrenzt"
    StatusEntry.objects.create(
        name="Approval",
        content=f"{user_name}: {wards} ist {limit} sichtbar",
        department=None,
        company_id=request.session["company_id"],
    )
    return JsonResponse(res, safe=False)


@ajax_login_required
def updates(request, last_change=0):
    return get_last_change_response(
        request.session["company_id"], int(last_change)
    )


@ajax_login_required
@require_POST
@permission_required("sp_app.is_dep_lead", raise_exception=True)
def change_function(request):
    """Change the ability of a person to perform a function.

    The data come in this form:
    {'person': person.shortname,
     'ward': ward.shortname,
     'add': True|False,
    }
    """
    data = json.loads(request.body)
    company_id = request.session["company_id"]
    res = {"status": "error"}
    try:
        person = Person.objects.get(id=data["person"], company_id=company_id)
        ward = Ward.objects.get(id=data["ward"], company_id=company_id)
        if data["add"]:
            person.functions.add(ward)
        else:
            person.functions.remove(ward)
        res = {
            "status": "ok",
            "person": person.shortname,
            "functions": [f.shortname for f in person.functions.all()],
        }
    except Person.DoesNotExist:
        res["reason"] = f'Person {data["person"]} not found'
    except Ward.DoesNotExist:
        res["reason"] = f'Ward {data["ward"]} not found'
    return JsonResponse(res, safe=False)


@ajax_login_required
def get_change_history(request, date, ward_id):
    """Get all changes to a staffing on one day and ward

    date: "YYYYMMDD"
    ward: <ward.id>
    """
    return JsonResponse(
        _get_change_history(request.session["company_id"], date, ward_id),
        safe=False,
    )


def _get_change_history(company_id, date, ward_id):
    day = datetime.strptime(date, "%Y%m%d").date()
    # Get all ChangeLoggings for this day or that include this day
    cls = (
        ChangeLogging.objects.filter(
            Q(continued=False, day=day)
            | Q(continued=True, day__lte=day, until__gte=day)
            | Q(continued=True, day__lte=day, until__isnull=True),
            company__id=company_id,
            ward__id=int(ward_id),
        )
        .select_related("user", "person", "ward")
        .order_by("-change_time")
    )
    return [c.get_json_for_history() for c in cls]


@ajax_login_required
@require_POST
@permission_required("sp_app.is_dep_lead", raise_exception=True)
def differentday(request, action, ward, day_id):
    # Make sure it's the right company
    ward = get_object_or_404(
        Ward, pk=ward, company__id=request.session["company_id"]
    )
    day = datetime.strptime(day_id, "%Y%m%d").date()
    try:
        dd = DifferentDay.objects.get(ward=ward, day=day)
        if action.startswith("add"):
            return JsonResponse(
                {
                    "status": "error",
                    "message": "There is a different planning already",
                }
            )
        if (dd.added and action == "remove_cancelation") or (
            not dd.added and action == "remove_additional"
        ):
            return JsonResponse({"status": "error", "message": "Wrong action"})
        DifferentDay.objects.filter(id=dd.id).delete()
        return JsonResponse({"status": "ok"})
    except DifferentDay.DoesNotExist:
        if action.startswith("remove"):
            return JsonResponse(
                {
                    "status": "error",
                    "message": "There is no different planning for this day",
                }
            )
        DifferentDay.objects.create(
            ward=ward, day=day, added=(action == "add_additional")
        )
        return JsonResponse({"status": "ok"})


# Setup ---------------------------------------------------------------


def setup_filter(request):
    if request.session.get("is_company_admin", False):
        return {"company_id": request.session["company_id"]}
    else:
        return {"departments__id__in": request.session["department_ids"]}


def persons_for_request(request):
    return Person.objects.filter(**setup_filter(request)).order_by(
        "position", "name"
    )


def wards_for_request(request):
    return (
        Ward.objects.filter(**setup_filter(request))
        .order_by("position", "name")
        .distinct()
    )


@ajax_login_required
def setup_departments(request):
    company = (
        Company.objects.select_related("region")
        .prefetch_related("departments")
        .get(id=request.session["company_id"])
    )
    return render(
        request,
        f"sp_app/setup/setup-pane.jinja",
        {"company": company, "current_tab": "departments"},
    )


@ajax_login_required
def setup_employees(request):
    employees = Employee.objects.select_related("user").filter(
        company__id=request.session["company_id"]
    )
    if not request.session.get("is_company_admin", False):
        employees = employees.exclude(_level="is_company_admin")
    return render(
        request,
        f"sp_app/setup/setup-pane.jinja",
        {"employees": employees, "current_tab": "employees"},
    )


@ajax_login_required
def setup_persons(request):
    persons = persons_for_request(request)
    return render(
        request,
        f"sp_app/setup/setup-pane.jinja",
        {
            "persons": persons,
            "former_persons": any(not p.current() for p in persons),
            "email_available": settings.EMAIL_AVAILABLE,
            "current_tab": "persons",
        },
    )


@ajax_login_required
def setup_wards(request):
    wards = wards_for_request(request)
    return render(
        request,
        f"sp_app/setup/setup-pane.jinja",
        {
            "wards": wards,
            "inactive_wards": any(not w.active for w in wards),
            "current_tab": "wards",
        },
    )


@ajax_login_required
def setup_zuordnung(request):
    persons = persons_for_request(request).prefetch_related("functions")
    wards = wards_for_request(request).filter(active=True)
    return render(
        request,
        f"sp_app/setup/setup-pane.jinja",
        {
            "persons": persons,
            "wards": list(wards),
            "no_mapping": len(persons) == 0 or len(wards) == 0,
            "current_tab": "zuordnung",
        },
    )


@ajax_login_required
@permission_required("sp_app.is_company_admin", raise_exception=True)
def edit_department(request, department_id=None):
    """Edit the department or create a new one

    Called with GET: return the form
    Called with POST: return nothing as form and the department list (oob)
    """
    company_id = request.session["company_id"]
    try:
        department = Department.objects.get(
            id=department_id, company_id=company_id
        )
        kwargs = {"instance": department}
    except Department.DoesNotExist:
        kwargs = {"initial": {"company": company_id}}
    form = forms.DepartmentForm(post_with_company(request), **kwargs)
    if form.is_valid():
        form.save()
        return setup_departments(request)
    return render(
        request,
        "sp_app/setup/edit_department.html",
        {
            "form": form,
            "url": reverse("department-update", args=(department_id,))
            if department_id
            else reverse("department-add"),
        },
    )


@ajax_login_required
@permission_required("sp_app.is_dep_lead", raise_exception=True)
def edit_employee(request, employee_id=None):
    """Edit the Employee or create a new one

    Called with GET: return the form
    Called with POST: return nothing als form and the object list (oob)
    If Employee is new: create user
    If Employee exists: edit user w/o password, maybe add ChangePasswordForm
    """
    company_id = request.session["company_id"]
    try:
        employee = Employee.objects.select_related("user").get(
            id=employee_id, company_id=company_id
        )
        emp_kwargs = {"instance": employee}
        user_kwargs = {"instance": employee.user}
    except Employee.DoesNotExist:
        employee = None
        emp_kwargs = {"initial": {"company": company_id}}
        user_kwargs = {}
    if not request.session.get("is_company_admin", False):
        emp_kwargs["departments"] = request.session["department_ids"]
        emp_kwargs["no_admin"] = True
    employee_form = forms.EmployeeForm(request.POST or None, **emp_kwargs)
    user_form = (
        forms.UserFormWithPassword if employee_id is None else forms.UserForm
    )(request.POST or None, **user_kwargs)
    if employee_form.is_valid() and user_form.is_valid():
        employee = employee_form.save(commit=False)
        employee.company_id = company_id
        employee.user = user_form.save()
        employee.save()
        employee_form.save_m2m()
        employee.set_level(employee_form.cleaned_data["lvl"] or None)

        return setup_employees(request)
    can_delete = employee is not None and employee.user != request.user
    return render(
        request,
        "sp_app/setup/edit_employee.html",
        {
            "user_form": user_form,
            "employee_form": employee_form,
            "url": reverse("employee-update", args=(employee_id,))
            if employee_id
            else reverse("employee-add"),
            "delete_url": reverse("employee-delete", args=(employee_id,))
            if can_delete
            else "",
            "employee": employee,
        },
    )


@ajax_login_required
@permission_required("sp_app.is_company_admin", raise_exception=True)
def delete_employee(request, employee_id):
    error, message = "", ""
    try:
        employee = Employee.objects.select_related("user").get(
            id=employee_id, company_id=request.session["company_id"]
        )
        if employee.user == request.user:
            error = "Aktive/r Bearbeiter/in kann nicht deaktiviert werden"
    except Employee.DoesNotExist:
        error = "Bearbeiter/in nicht gefunden"
    if not error:
        employee.user.is_active = False
        employee.user.save()
        message = f"{employee.get_name()} kann sich nicht mehr als Bearbeiter/in anmelden"

    return render(
        request,
        "sp_app/setup/message_or_error.jinja",
        {"message": message, "error": error},
    )


@ajax_login_required
@permission_required("sp_app.is_dep_lead", raise_exception=True)
def edit_person(request, pk=None):
    """Edit the department or create a new one

    Called with GET: return the form
    Called with POST: return nothing als form and the department list (oob)
    """
    company_id = request.session["company_id"]
    person = pk and Person.objects.get(pk=pk, company_id=company_id)
    if person is None:
        kwargs = {"initial": {"company": company_id}}
    else:
        kwargs = {"instance": person}
    if not request.session.get("is_company_admin", False):
        kwargs["departments"] = request.session["department_ids"]
    form = forms.PersonForm(post_with_company(request), **kwargs)
    if form.is_valid():
        form.save()
        return setup_persons(request)
    return render(
        request,
        "sp_app/setup/edit_person.jinja",
        {
            "form": form,
            "url": reverse("person-update", args=(pk,))
            if pk
            else reverse("person-add"),
        },
    )


@ajax_login_required
@permission_required("sp_app.is_dep_lead", raise_exception=True)
def edit_ward(request, pk=None):
    """Edit the department or create a new one

    Called with GET: return the form
    Called with POST: return nothing als form and the department list (oob)
    """
    company_id = request.session["company_id"]
    ward = pk and Ward.objects.get(pk=pk, company_id=company_id)
    if ward is None:
        kwargs = {"initial": {"company": company_id}}
    else:
        kwargs = {"instance": ward}
    if not request.session.get("is_company_admin", False):
        kwargs["departments"] = request.session["department_ids"]
    form = forms.WardForm(post_with_company(request), **kwargs)
    if form.is_valid():
        form.save()
        return setup_wards(request)
    return render(
        request,
        "sp_app/setup/edit_ward.jinja",
        {
            "form": form,
            "url": reverse("ward-update", args=(pk,))
            if pk
            else reverse("ward-add"),
        },
    )


@ajax_login_required
@require_POST
@permission_required("sp_app.is_dep_lead", raise_exception=True)
def edit_mapping(request, person_id, ward_id, possible):
    """Change the ability of a person to perform a function."""
    company_id = request.session["company_id"]
    try:
        person = Person.objects.get(id=person_id, company_id=company_id)
        ward = Ward.objects.get(id=ward_id, company_id=company_id)
        if possible:
            person.functions.add(ward)
        else:
            person.functions.remove(ward)
        return render(
            request,
            "sp_app/setup/lists/zuordnung-detail.jinja",
            {"person": person, "ward": ward, "possible": possible},
        )
    except Person.DoesNotExist:
        reason = f"Person {person_id} not found"
    except Ward.DoesNotExist:
        reason = f"Ward {ward_id} not found"
    # TODO: add logging
    assert False


ICAL_MAIL_TEXT = """
Guten Tag!

Für "{}" wurde mit "Stationsplan.de" ein Online-Kalender mit den
geplanten Diensten erstellt. Die Adresse ist

    https://stationsplan.de{}

Importieren Sie diese Adresse in Ihre Kalender-App Ihres Smartphones oder
Computers.

Sollte diese Mail nicht für Sie gedacht gewesen sein, können Sie sie
einfach ignorieren.

Mit freundlichen Grüßen, Stationsplan.de
"""


@ajax_login_required
@permission_required("sp_app.is_dep_lead")
def send_ical_feed(request, pk):
    """Send the url of the personal feed to the person's mail address"""

    def response(msg):
        return HttpResponse(f"<td>{msg}</td>")

    if not settings.EMAIL_AVAILABLE:
        return response("No Mailservice")
    department_ids = request.session.get("department_ids")
    person = get_object_or_404(
        Person, pk=pk, departments__id__in=department_ids
    )
    if not person.email:
        return response("Mailadresse fehlt")
    feed_id = person.feed_ids.order_by("pk").last()
    if feed_id is None:
        feed_id = FeedId.new(person)

    subject = f"Kalender für {person.name}"
    url = reverse("icalfeed", kwargs={"feed_id": feed_id.uid})
    success = send_mail(
        subject,
        ICAL_MAIL_TEXT.format(person.name, url),
        "server@stationsplan.de",
        [person.email],
        fail_silently=False,
    )
    if success:
        return response("Mail versandt")
    else:
        return response("Error")
