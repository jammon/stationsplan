# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView, UpdateView

from sp_app import forms, business_logic
from .models import Person, Ward
from .utils import get_first_of_month


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
    return render(request, 'sp_app/plan.html',
                  business_logic.get_plan_data(request.session, month, day))


class DepLeadRequiredMixin(PermissionRequiredMixin):
    permission_required = 'sp_app.is_dep_lead'


class PersonenView(DepLeadRequiredMixin, ListView):
    context_object_name = 'personen'

    def get_queryset(self):
        department_ids = self.request.session.get('department_ids')
        return Person.objects.filter(
            departments__id__in=department_ids
        ).order_by('position', 'name')


class FunktionenView(DepLeadRequiredMixin, ListView):
    model = Ward
    ordering = ['position', 'name']


class PersonMixin(DepLeadRequiredMixin):
    model = Person
    form_class = forms.PersonForm
    success_url = '/zuordnung'


class PersonCreateView(PersonMixin, CreateView):

    def get_initial(self):
        return {
            'company': self.request.session['company_id'],
            'start_date': get_first_of_month(),
        }


class PersonUpdateView(PersonMixin, UpdateView):
    pass


class WardMixin(DepLeadRequiredMixin):
    model = Ward
    form_class = forms.WardForm
    success_url = '/zuordnung'


class WardCreateView(WardMixin, CreateView):

    def get_initial(self):
        return {
            'company': self.request.session['company_id'],
        }


class WardUpdateView(WardMixin, UpdateView):
    pass
