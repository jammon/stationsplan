# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
from datetime import datetime, date
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import render
from django.views.generic.base import TemplateView

from .models import Person, Ward, ChangeLogging, ChangingStaff, date_to_json
from .utils import get_past_changes, changes_for_month, get_for_company


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


@login_required
def month(request):
    department_ids = request.session.get('department_ids')
    wards = Ward.objects.filter(departments__id__in=department_ids)
    year = int(request.GET['year'])
    month = int(request.GET['month'])
    data = changes_for_month(date(year, month, 1), wards)
    # data['can_change'] = request.user.has_perm('sp_app.add_changingstaff')
    return JsonResponse(data, safe=False)


def tests(request):
    return render(request, 'sp_app/tests.html', {})


@login_required
def change(request):
    """One *person* is
    added to or removed (*action*)
    on one *day*
    from the staffing of one *ward*
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    person = get_for_company(Person, request, shortname=request.POST['person'])
    ward = get_for_company(Ward, request, shortname=request.POST['ward'])
    day = datetime.strptime(request.POST['day'], '%Y%m%d').date()
    added = request.POST['action'] == 'add'
    ChangeLogging.objects.create(
        company_id=request.session['company_id'], user=request.user,
        person=person, ward=ward, day=day, added=added)
    ch_st, created = ChangingStaff.objects.get_or_create(
        person=person, ward=ward, day=day, defaults={'added': added})
    if created:
        return JsonResponse({'success': True})
    else:
        if ch_st.added != added:
            ChangingStaff.objects.filter(pk=ch_st.pk).delete()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'warning': "Change is already in database"})
