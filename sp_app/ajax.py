# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.http import (HttpResponseNotAllowed, JsonResponse)

import json

from .models import Person, Ward, ChangeLogging
from .utils import get_for_company


@login_required
def changes(request):
    """Some *person*s are added to or removed (*action*)
    from the staffing of a *ward*
    on a *day*
    for a *single_day* or for the future
    The data come in this form:
    {'day': <YYYYMMDD>,
     'ward': <ward.shortname>,
     'continued': True|False,
     'persons': [{
           'id': <person.shortname>,
           'action': 'add'|'remove',
         },
         ...
     ]}

    There is no testing, whether the same change is already in the database.
    The frontend has to deal with this.
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    company_id = request.session['company_id']
    try:
        print(request.body)
        data = json.loads(request.body)
        print(data)
        print(repr(data))
        day = datetime.strptime(data['day'], '%Y%m%d').date()
        ward = get_for_company(Ward, request, shortname=data['ward'])
        persons = dict(
            (person.shortname, person) for person in
            Person.objects.filter(
                company__id=company_id,
                shortname__in=(p['id'] for p in data['persons'])))
        for p in data['persons']:
            if p['id'] not in persons:
                return JsonResponse({
                    'error': "Person '{}' not found".format(p['id'])})
        cls = []
        for p in data['persons']:
            cls.append(ChangeLogging.objects.create(
                company_id=company_id,
                user=request.user,
                person=persons[p['id']],
                ward=ward,
                day=day,
                added=p['action'] == 'add',
                continued=data['continued']))
        return JsonResponse([json.loads(cl.json) for cl in cls], safe=False)
    except ValueError as e:
        raise e
