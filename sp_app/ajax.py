# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse

import json

from .utils import apply_changes, set_approved, get_last_change
from .models import StatusEntry, ChangeLogging


@login_required
@require_POST
@permission_required('sp_app.add_changelogging', raise_exception=True)
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
    data = json.loads(request.body)
    cls = apply_changes(request.user, request.session['company_id'], **data)
    return JsonResponse(cls, safe=False)


@login_required
@require_POST
@permission_required('sp_app.add_changelogging', raise_exception=True)
def change_approved(request):
    """Set the approved date for a ward.

    The data come in this form:
    {'wards': [<ward.shortname>, ...]
     'date': False|<YYYYMMDD>,
    }
    """
    data = json.loads(request.body)
    res = set_approved(data['wards'], data['date'],
                       request.session['company_id'])
    template = ('{user_name}: {wards} ist {limit} sichtbar')
    content = template.format(
        user_name=request.user.last_name or request.user.get_username(),
        wards=', '.join(res['wards']),
        limit=('bis ' + res['approved']) if res['approved'] else 'unbegrenzt')
    StatusEntry.objects.create(
        name='Approval',
        content=content,
        department=None,
        company_id=request.session['company_id'])
    return JsonResponse(res, safe=False)


@login_required
# TODO: zweiten DB-Zugriff entfernen
def updates(request, last_change=0):
    cl = ChangeLogging.objects.filter(
        company_id=request.session['company_id'],
        pk__gt=last_change
    ).values_list('json', flat=True).order_by('pk')
    if len(cl) == 0:
        return JsonResponse({})
    return JsonResponse({
        'cls': [json.loads(cljson) for cljson in cl],
        'last_change': get_last_change(request.session['company_id'])
    })
