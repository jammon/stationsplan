# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
from datetime import date, timedelta
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .models import Person, Ward, Planning
from .utils import (get_first_of_month, json_array)


def home(request):
    if request.user.is_authenticated():
        return redirect('plan')
    return render(request, "sp_app/index.html", context={'next': '/plan'})


@login_required
def plan(request, month='', day=''):
    # month is '' or 'YYYYMM'
    # day is '' or 'YYYYMMDD' or None (for path "/tag")
    if month == '' and day:
        month = day[:6]
    department_ids = request.session.get('department_ids')
    # Get all Persons who worked here in this month
    first_of_month = get_first_of_month(month)
    # start_of_data should be three months earlier
    start_of_data = (first_of_month - timedelta(88)).replace(day=1)
    persons = Person.objects.filter(
        end_date__gte=start_of_data,
        departments__id__in=department_ids
    ).prefetch_related('functions')
    wards = Ward.objects.filter(departments__id__in=department_ids)
    can_change = request.user.has_perm('sp_app.add_changelogging')
    plannings = Planning.objects.filter(
        ward__in=wards,
        end__gte=start_of_data,
        superseded_by=None).select_related('ward')
    if not can_change:
        plannings = [p for p in plannings
                     if not p.ward.approved or p.start <= p.ward.approved]
    data = {
        'persons': json.dumps([p.toJson() for p in persons]),
        'wards': json_array(wards),
        'plannings': json_array(plannings),
        'user': request.user,
        'can_change': 'true'if can_change else 'false',
        'first_of_month': first_of_month,
        'start_of_data': start_of_data,
    }
    if first_of_month > date.today():
        data['prev_month'] = (first_of_month - timedelta(1)).strftime('%Y%m')
    return render(request, 'sp_app/plan.html', data)


@login_required
def previous_months(request):
    pass


@login_required
def password_change(request):
    return auth_views.password_change(
        request, template_name='registration/password_change.html',
        post_change_redirect='/plan')


def tests(request):
    return render(request, 'sp_app/tests.html', {})
