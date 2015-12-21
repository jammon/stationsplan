# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
from datetime import datetime, date
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.generic.base import TemplateView

from .models import Person, Ward, date_to_json
from .utils import get_past_changes, changes_for_month


class HomePageView(TemplateView):
    template_name = "sp_app/index.html"


@login_required
def plan(request, month):
    department_ids = request.session.get('department_ids')
    try:
        first_of_month = datetime.strptime(month, '%Y%m').date()
    except (TypeError, ValueError):
        first_of_month = date.today().replace(day=1)
    # Get all Persons who worked here from last month to in one year
    persons = Person.objects.filter(
        start_date__lt=first_of_month.replace(year=first_of_month.year+1),
        end_date__gt=first_of_month.replace(month=1),
        departments__id__in=department_ids
    ).prefetch_related('functions')
    wards = dict(
        (ward['id'], ward) for ward in
        Ward.objects.filter(departments__id__in=department_ids).values())
    for ward in wards.values():
        if ward['approved']:
            ward['approved'] = date_to_json(ward['approved'])
    special_duties = Ward.after_this.through.objects.filter(
        from_ward__company_id=request.session['company_id'])
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
    }
    return render(request, 'sp_app/plan.html', data)


def tests(request):
    return render(request, 'sp_app/tests.html', {})
