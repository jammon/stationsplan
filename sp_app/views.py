# -*- coding: utf-8 -*-
import json
import pytz
from datetime import date, timedelta, datetime
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import ListView, CreateView, UpdateView

from sp_app import forms
from .models import (Person, Ward, DifferentDay, Planning, ChangeLogging,
                     Department)
from .utils import (get_first_of_month, json_array, get_holidays_for_company)


def home(request):
    if request.user.is_authenticated:
        return redirect('plan')
    return render(request, "sp_app/index.html", context={'next': '/plan'})


@login_required
def plan(request, month='', day=''):
    """ Delivers all the data to built the month-, day- and on-call-view
    on the client side.

    This view is called by 'plan', 'dienste', and 'tag'.

    month is '' or 'YYYYMM'
    day is '' or 'YYYYMMDD' or None (for path "/tag")
    """
    if month == '' and day:
        month = day[:6]
    department_ids = request.session.get('department_ids')
    company_id = request.session.get('company_id')
    # Get all Persons who work here currently
    first_of_month = get_first_of_month(month)
    # start_of_data should be one month earlier
    start_of_data = (first_of_month - timedelta(28)).replace(day=1)
    persons = Person.objects.filter(
        end_date__gte=start_of_data,
        company_id=company_id
    ).prefetch_related('functions')
    wards = Ward.objects.filter(departments__id__in=department_ids)
    different_days = DifferentDay.objects.filter(
        ward__departments__id__in=department_ids,
        day__gte=start_of_data).select_related('ward')
    plannings = Planning.objects.filter(
        ward__in=wards,
        end__gte=start_of_data,
        superseded_by=None).select_related('ward')

    is_editor = request.session.get('is_editor', False)
    if not is_editor:
        plannings = [p for p in plannings
                     if not p.ward.approved or p.start <= p.ward.approved]
    holidays = get_holidays_for_company(request.session['company_id'])
    departments = dict(
        (d.id, d.name) for d in
        Department.objects.filter(id__in=department_ids))
    data = {
        'persons': json.dumps([p.toJson() for p in persons]),
        'wards': json.dumps([w.toJson() for w in wards]),
        'different_days': json.dumps([
            (dd.ward.shortname,
             dd.day.strftime('%Y%m%d'),
             '+' if dd.added else '-')
            for dd in different_days]),
        'plannings': json_array(plannings),
        'user': request.user,
        'is_editor': is_editor,
        'first_of_month': first_of_month,
        'start_of_data': start_of_data,
        'holidays': json.dumps([h.toJson() for h in holidays]),
        'departments': json.dumps(departments),
    }
    last_change = ChangeLogging.objects.filter(
        company_id=request.session['company_id'],
    ).values('pk', 'change_time').order_by('pk').last()
    if last_change is not None:
        time_diff = datetime.now(pytz.utc) - last_change['change_time']
        data['last_change_pk'] = last_change['pk']
        data['last_change_time'] = time_diff.days * 86400 + time_diff.seconds

    if first_of_month > date.today():
        data['prev_month'] = (first_of_month - timedelta(1)).strftime('%Y%m')
    return render(request, 'sp_app/plan.html', data)


class PersonenView(ListView):
    context_object_name = 'personen'

    def get_queryset(self):
        department_ids = self.request.session.get('department_ids')
        return Person.objects.filter(
            departments__id__in=department_ids
        ).order_by('position', 'name')


class FunktionenView(ListView):
    model = Ward
    ordering = ['position', 'name']


class PersonMixin:
    model = Person
    form_class = forms.PersonForm


class PersonCreateView(PersonMixin, CreateView):
    success_url = '/zuordnung'

    def get_initial(self):
        return {
            'company_id': self.request.session['company_id']
        }


class PersonUpdateView(PersonMixin, UpdateView):
    success_url = '/personen'

