# -*- coding: utf-8 -*-
from collections import defaultdict
from datetime import datetime
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.http import JsonResponse, QueryDict
from functools import wraps

import json
import re

from .utils import apply_changes, set_approved, get_last_change_response
from .models import StatusEntry, Person, Ward, ChangeLogging


def ajax_login_required(function=None):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied
        return function(request, *args, **kwargs)
    return _wrapped_view


@ajax_login_required
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
    data = QueryDict(request.body)
    prog = re.compile("persons\[(\d+)\]\[(\w+)\]")
    persons = defaultdict(dict)
    for key, value in data.items():
        match = prog.search(key)
        if match:
            persons[int(match.group(1))][match.group(2)] = value
    company_id = request.session['company_id']
    apply_changes(
        request.user, company_id, data['day'], data['ward_id'],
        data['continued'], persons.values())
    return get_last_change_response(company_id, int(data['last_pk']))


@ajax_login_required
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
                       request.session['department_ids'])
    user_name = request.user.last_name or request.user.get_username()
    wards = ', '.join(res['wards'])
    limit = ('bis ' + res['approved']) if res['approved'] else 'unbegrenzt'
    StatusEntry.objects.create(
        name='Approval',
        content=f'{user_name}: {wards} ist {limit} sichtbar',
        department=None,
        company_id=request.session['company_id'])
    return JsonResponse(res, safe=False)


@ajax_login_required
def updates(request, last_change=0):
    return get_last_change_response(
        request.session['company_id'], int(last_change))


@ajax_login_required
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
    except Person.DoesNotExist:
        res['reason'] = f'Person {data["person"]} not found'
    except Person.MultipleObjectsReturned:
        res['reason'] = f'Person {data["person"]} found multiple times'
    except Ward.DoesNotExist:
        res['reason'] = f'Ward {data["ward"]} not found'
    except Ward.MultipleObjectsReturned:
        res['reason'] = f'Ward {data["ward"]} found multiple times'
    return JsonResponse(res, safe=False)


@ajax_login_required
def change_history(request, date, ward_id):
    """Get all changes to a staffing on one day and ward

    date: "YYYYMMDD"
    ward: <ward.id>
    """
    day = datetime.strptime(date, '%Y%m%d').date()
    # Get all ChangeLoggings for this day or that include this day
    cls = ChangeLogging.objects.filter(
        Q(continued=False, day=day) |
        Q(continued=True, day__lte=day, until__gte=day) |
        Q(continued=True, day__lte=day, until__isnull=True),
        company__id=request.session['company_id'],
        ward__id=int(ward_id),
    ).select_related('user', 'person', 'ward').order_by('-change_time')
    return JsonResponse([{
        'user': c.user.get_full_name() or c.user.get_username(),
        'person': c.person.shortname,
        'ward': c.ward.shortname,
        'day': c.day,
        'added': c.added,
        'continued': c.continued,
        'until': c.until,
        'change_time': c.change_time,
    } for c in cls], safe=False)
