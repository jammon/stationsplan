# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotAllowed, JsonResponse

from .models import Person, Ward, ChangeLogging
from .utils import get_for_company


@login_required
def change(request):
    """One *person* is
    added to or removed (*action*)
    on one *day*
    from the staffing of one *ward*

    There is no testing, whether the same change is already in the database.
    The frontend has to deal with this.
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
    return JsonResponse({'success': True})
