# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth.decorators import login_required
from django.http import (HttpResponseNotAllowed, HttpResponseForbidden,
                         JsonResponse)

import json

from .utils import apply_changes


@login_required
def changes(request):
    """Some *person*s are added to or removed (*action*)
    from the staffing of a *ward*
    on a *day*
    for a *single_day* or for the future
    The data come in this form:
    {'day': <YYYYMMDD>,
     'ward': <ward.shortname>,
     'continued': True|False|<YYYYMMDD>,
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
    if not request.user.has_perm('sp_app.add_changelogging'):
        return HttpResponseForbidden()
    data = json.loads(request.body)
    cls = apply_changes(request.user, request.session['company_id'], **data)
    return JsonResponse(cls, safe=False)
