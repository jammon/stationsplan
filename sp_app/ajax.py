# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from datetime import datetime, date
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotAllowed, JsonResponse
from django.views.generic.base import TemplateView

from .models import Person, Ward, ChangeLogging, ChangingStaff
from .utils import changes_for_month, get_for_company


class HomePageView(TemplateView):
    template_name = "sp_app/index.html"


@login_required
def month(request):
    department_ids = request.session.get('department_ids')
    wards = Ward.objects.filter(departments__id__in=department_ids)
    year = int(request.GET['year'])
    month = int(request.GET['month'])
    data = changes_for_month(date(year, month, 1), wards)
    # data['can_change'] = request.user.has_perm('sp_app.add_changingstaff')
    return JsonResponse(data, safe=False)


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
