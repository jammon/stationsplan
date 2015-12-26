# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
from datetime import datetime, date, timedelta
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .models import Person, Ward, date_to_json
from .utils import get_past_changes, changes_for_month


def home(request):
    if request.user.is_authenticated():
        return redirect('plan')
    return render(request, "sp_app/index.html")


@login_required
def plan(request, month=''):
    department_ids = request.session.get('department_ids')
    try:
        first_of_month = datetime.strptime(month, '%Y%m').date()
    except (TypeError, ValueError):
        first_of_month = date.today().replace(day=1)
    # Get all Persons who worked here in this month
    persons = Person.objects.filter(
        start_date__lt=(first_of_month+timedelta(32)).replace(day=1),
        end_date__gte=first_of_month,
        departments__id__in=department_ids
    ).prefetch_related('functions')
    wards = dict(
        (ward['id'], ward) for ward in
        Ward.objects.filter(departments__id__in=department_ids).values())
    for ward in wards.values():
        if ward['approved']:
            ward['approved'] = date_to_json(ward['approved'])
    special_duties = Ward.after_this.through.objects.filter(
        from_ward__company_id=request.session['company_id']
    ).select_related('from_ward', 'to_ward')
    for sp in special_duties:
        ward = wards.get(sp.from_ward.id)
        if ward:
            aft = ward.get('after_this')
            if aft:
                ward['after_this'] = ','.join((aft, sp.to_ward.shortname))
            else:
                ward['after_this'] = sp.to_ward.shortname
    name = request.user.get_full_name() or request.user.get_username()
    data = {
        'persons': json.dumps([p.toJson() for p in persons]),
        'wards': json.dumps(wards.values()),
        'past_changes': json.dumps(get_past_changes(first_of_month, wards)),
        'changes': json.dumps(changes_for_month(first_of_month, wards)),
        'year': first_of_month.year,
        'month': first_of_month.month,
        'user': request.user,
        'name': name,
        'can_change': 1 if request.user.has_perm('sp_app.add_changingstaff') else 0,
        'next_month': (first_of_month + timedelta(32)).strftime('%Y%m'),
        'month_heading': first_of_month.strftime('%B %Y'),
        'first_of_month': first_of_month,
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
