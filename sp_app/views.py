# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
from datetime import datetime, date, timedelta
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .models import Person, Ward, date_to_json
from .utils import (get_past_changes, changes_for_month_as_json,
    get_first_of_month)


def home(request):
    if request.user.is_authenticated():
        return redirect('plan')
    return render(request, "sp_app/index.html")


@login_required
def plan(request, month='', ward_selection=''):
    department_ids = request.session.get('department_ids')
    # Get all Persons who worked here in this month
    first_of_month = get_first_of_month(month)
    persons = Person.objects.filter(
        start_date__lt=(first_of_month+timedelta(32)).replace(day=1),
        end_date__gte=first_of_month,
        departments__id__in=department_ids
    ).prefetch_related('functions')
    wards = Ward.objects.filter(departments__id__in=department_ids
               ).values('id', 'json')
    if ward_selection=='noncontinued':
        wards = wards.filter(continued=False)
    wards_ids = [w['id'] for w in wards]
    wards_json = '[' + ', '.join(w['json'] for w in wards) + ']'
    name = request.user.get_full_name() or request.user.get_username()
    data = {
        'persons': json.dumps([p.toJson() for p in persons]),
        'wards': wards_json,
        'past_changes': json.dumps(get_past_changes(first_of_month, wards_ids)),
        'changes': changes_for_month_as_json(first_of_month, wards_ids),
        'year': first_of_month.year,
        'month': first_of_month.month,
        'user': request.user,
        'name': name,
        'can_change': 1 if request.user.has_perm('sp_app.add_changelogging') else 0,
        'next_month': (first_of_month + timedelta(32)).strftime('%Y%m'),
        'month_heading': first_of_month.strftime('%B %Y'),
        'first_of_month': first_of_month,
        'ward_selection': ward_selection,
    }
    if first_of_month > date.today():
        data['prev_month'] = (first_of_month - timedelta(1)).strftime('%Y%m')
    return render(request, 'sp_app/plan.html', data)


@login_required
def password_change(request):
    # return auth_views.password_change(request)
    return auth_views.password_change(
        request, template_name='registration/password_change.html',
        post_change_redirect='/plan')


def tests(request):
    return render(request, 'sp_app/tests.html', {})
