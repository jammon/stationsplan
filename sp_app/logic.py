# -*- coding: utf-8 -*-
"""The business logic"""
import json
import logging
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from http import HTTPStatus
from numbers import Number
from datetime import timedelta, datetime

from .models import (
    FAR_FUTURE,
    CalculatedHoliday,
    Company,
    Employee,
    Person,
    Ward,
    DifferentDay,
    Planning,
    ChangeLogging,
    Department,
    process_change,
)
from .utils import get_first_of_month, time_since


def get_plan_data(
    company_id,
    department_ids,
    month="",
    day="",
    is_editor=False,
    is_dep_lead=False,
    is_company_admin=False,
):
    """Produce data for views.plan

    month is '' or 'YYYYMM'
    day is '' or 'YYYYMMDD' or None (for path "/tag")
    """
    if month == "" and day:
        month = day[:6]
    # Get all Persons who work here currently
    first_of_month = get_first_of_month(month)
    # start_of_data should be one month earlier
    start_of_data = (first_of_month - timedelta(28)).replace(day=1)
    persons_qs = (
        Person.objects.filter(company_id=company_id)
        .order_by("position", "name")
        .prefetch_related("functions", "departments")
    )
    wards = Ward.objects.filter(
        departments__id__in=department_ids
    ).prefetch_related("after_this", "not_with_this")
    if len(persons_qs) == 0 or len(wards) == 0:
        return None
    different_days = DifferentDay.objects.filter(
        ward__departments__id__in=department_ids, day__gte=start_of_data
    ).select_related("ward")
    plannings = Planning.objects.filter(
        ward__in=wards,
        ward__active=True,
        end__gte=start_of_data,
        superseded_by=None,
    ).select_related("ward")

    if not is_editor:
        plannings = [
            p
            for p in plannings
            if not p.ward.approved or p.start <= p.ward.approved
        ]
    holidays = get_holidays_for_company(company_id)
    departments = dict(
        (d.id, d.name)
        for d in Department.objects.filter(id__in=department_ids)
    )
    data = {
        "persons": [
            p.toJson() for p in persons_qs if p.end_date >= start_of_data
        ],
        "wards": [w.toJson() for w in wards if w.active],
        "different_days": [
            (
                dd.ward.shortname,
                dd.day.strftime("%Y%m%d"),
                "+" if dd.added else "-",
            )
            for dd in different_days
        ],
        "plannings": [p.toJson() for p in plannings],
        "is_editor": is_editor,
        "is_dep_lead": is_dep_lead,
        "is_company_admin": is_company_admin,
        "data_year": start_of_data.year,
        "data_month": start_of_data.month - 1,
        "holidays": [h.toJson() for h in holidays],
        "departments": departments,
    }
    last_change = (
        ChangeLogging.objects.filter(
            company_id=company_id,
        )
        .values("pk", "change_time")
        .order_by("pk")
        .last()
    )
    if last_change is not None:
        data["last_change_pk"] = last_change["pk"]
        data["last_change_time"] = int(
            time_since(last_change["change_time"]).total_seconds()
        )

    return {
        "data": json.dumps(data),
        "former_persons": [
            p for p in persons_qs if p.end_date < start_of_data
        ],
        "inactive_wards": [w for w in wards if not w.active],
    }


def get_for_company(klass, request=None, company_id="", **kwargs):
    """Return a model for this company

    Raises Http404 if not found
    """
    if request is None:
        return get_object_or_404(klass, company__id=company_id, **kwargs)
    return get_object_or_404(
        klass, company__id=request.session["company_id"], **kwargs
    )


def get_holidays_for_company(company_id):
    return CalculatedHoliday.objects.filter(regions__companies__id=company_id)


def apply_changes(user, company_id, day, ward_id, continued, persons):
    """Apply changes for this day and ward.
    Return a list of dicts of effective changes to be returned to the client
    'persons' is a list of dicts like
    {'id': <id>,
     'action': ‘add'|'remove'}
    """
    ward = get_for_company(Ward, company_id=company_id, id=ward_id)
    known_persons = {
        person.id: person
        for person in Person.objects.filter(
            company__id=company_id, id__in=(p["id"] for p in persons)
        )
    }
    data = dict(
        company_id=company_id,
        user=user,
        ward=ward,
        day=datetime.strptime(day, "%Y%m%d").date(),
        continued=continued,
        until=None,
    )
    if isinstance(continued, str):
        data["until"] = datetime.strptime(continued, "%Y%m%d").date()
        data["continued"] = True
    cls = []
    for p in persons:
        p_id = int(p["id"])
        # TODO: log error
        assert p_id in known_persons, f"{p_id} is not in the persons database"
        cl = ChangeLogging.objects.create(
            person=known_persons[p_id], added=p["action"] == "add", **data
        )
        cl_dict = process_change(cl)
        if cl_dict:
            cls.append(cl_dict)
    if len(cls):
        set_cached_last_change_pk(max(cl["pk"] for cl in cls), company_id)
    return cls


def set_approved(wards, approved, department_ids):
    """
    wards is [<ward.shortname>, ...],
    approved is False|<YYYYMMDD>, (False means unlimited approval)
    company_id is <company.id>

    Only the wards of the given departments are approved
    """
    to_approve = Ward.objects.filter(
        departments__id__in=department_ids, shortname__in=wards
    )
    approval = (
        datetime.strptime(approved, "%Y%m%d").date()
        if approved
        else FAR_FUTURE
    )
    to_approve.update(approved=approval)
    to_approve_sn = [w.shortname for w in to_approve]
    return {
        "wards": to_approve_sn,
        "approved": approved,
        "not approved wards": [
            ward for ward in wards if ward not in to_approve_sn
        ],
    }


def get_cached_last_change_pk(company_id):
    """Returns the pk of the last changelogging or None if not set"""
    return cache.get(f"last_change_pk-{company_id}")


def set_cached_last_change_pk(last_change_pk, company_id):
    """Sets the pk of the last changelogging"""
    return cache.set(f"last_change_pk-{company_id}", last_change_pk)


def get_last_change_response(company_id, last_change_pk):
    """Return a JsonResponse with the changes since last_change_pk
    and pk and elapsed time of the last change.
    """
    assert isinstance(last_change_pk, Number)
    _lc_pk = get_cached_last_change_pk(company_id)
    if _lc_pk and (_lc_pk == last_change_pk):
        # Nothing changed
        return JsonResponse({}, status=HTTPStatus.NOT_MODIFIED)

    # get all ChangeLoggings since and including last_change_pk
    cls = list(
        ChangeLogging.objects.filter(
            company_id=company_id, pk__gte=last_change_pk
        ).order_by("pk")
    )
    if len(cls) == 0:
        # Only older ChangeLoggings, so last_change_pk is wrong
        cls = [ChangeLogging.objects.order_by("pk").last()]
        if len(cls) == 0:
            # No ChangeLoggings
            logging.debug("No ChangeLoggings found")
            return JsonResponse({}, status=HTTPStatus.NOT_MODIFIED)
    if cls[0].pk == last_change_pk:
        if len(cls) == 1:
            # No newer ChangeLoggings
            return JsonResponse({}, status=HTTPStatus.NOT_MODIFIED)
        cls = cls[1:]
    last_cl = cls[-1]
    time_diff = time_since(last_cl.change_time)
    if _lc_pk is None:
        # Set cache
        set_cached_last_change_pk(last_cl.pk, company_id)
    return JsonResponse(
        {
            "cls": [
                json.loads(cl.json) if cl.json else cl.toJson() for cl in cls
            ],
            "last_change": {
                "pk": last_cl.pk,
                "time": time_diff.days * 86400 + time_diff.seconds,
            },
        }
    )


def send_activation_mail(user):
    "send activation mail in the signup process"
    # don't send mails out of playwright tests
    if user.email.startswith("_pwt_"):
        return
    mail_subject = "Benutzerkonto für Stationsplan.de aktivieren"
    message = render_to_string(
        "sp_app/signup/activation_mail.txt",
        {
            "username": user.get_full_name() or user.get_username(),
            "uid": user.pk,
            "token": default_token_generator.make_token(user),
        },
    )
    send_mail(mail_subject, message, settings.SERVER_EMAIL, [user.email])


# Tests ------------------------------------------------------
