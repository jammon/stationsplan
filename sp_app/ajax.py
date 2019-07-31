# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse

import json

from .utils import apply_changes, set_approved, get_last_changes
from .models import StatusEntry, Person, Ward


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
     'ward_id': <ward.id>,
     'continued': True|False|<YYYYMMDD>,
     'persons': [{
           'id': <person.id>,
           'action': 'add'|'remove',
         },
         ...
     ],
     'last_pk': <ChangeLogging.pk>}

    Returned are the new changes since 'last_pk',
    including the just transmitted changes, if they succeeded.
    """
    data = json.loads(request.body)
    company_id = request.session['company_id']
    apply_changes(
        request.user, company_id, data['day'], data['ward_id'],
        data['continued'], data['persons'])
    return get_last_changes(company_id, data['last_pk'])


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
def updates(request, last_change=0):
    return get_last_changes(request.session['company_id'], last_change)


@login_required
@require_POST
@permission_required('sp_app.add_person', raise_exception=True)
def change_function(request):
    """Change the ability of a person to perform a function.

    The data come in this form:
    {'person': person.shortname,
     'ward': ward.shortname,
     'add': True|False,
    }
    """
    data = json.loads(request.body)
    company_id = request.session['company_id']
    res = {'status': 'error'}
    try:
        person = Person.objects.get(
            shortname=data['person'], company_id=company_id)
        ward = Ward.objects.get(shortname=data['ward'], company_id=company_id)
        if data['add']:
            person.functions.add(ward)
        else:
            person.functions.remove(ward)
        res = {
            'status': 'ok',
            'person': person.shortname,
            'functions': [f.shortname for f in person.functions.all()],
        }
    except Person.DoesNotExist as e:
        res['reason'] = 'Person {} not found'.format(data['person'])
    except Person.MultipleObjectsReturned as e:
        res['reason'] = 'Person {} found multiple times'.format(data['person'])
    except Ward.DoesNotExist as e:
        res['reason'] = 'Ward {} not found'.format(data['ward'])
    except Ward.MultipleObjectsReturned as e:
        res['reason'] = 'Ward {} found multiple times'.format(data['ward'])
    return JsonResponse(res, safe=False)
