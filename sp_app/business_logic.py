# -*- coding: utf-8 -*-
import json
import pytz
from datetime import timedelta, datetime

from .models import (Person, Ward, DifferentDay, Planning, ChangeLogging,
                     Department)
from .utils import (get_first_of_month, get_holidays_for_company)


def get_plan_data(session, month='', day=''):
    """ Produce data for views.plan

    month is '' or 'YYYYMM'
    day is '' or 'YYYYMMDD' or None (for path "/tag")
    """
    if month == '' and day:
        month = day[:6]
    department_ids = session.get('department_ids')
    company_id = session.get('company_id')
    # Get all Persons who work here currently
    first_of_month = get_first_of_month(month)
    # start_of_data should be one month earlier
    start_of_data = (first_of_month - timedelta(28)).replace(day=1)
    persons_qs = Person.objects.filter(company_id=company_id).order_by(
        'position', 'name').prefetch_related('functions', 'departments')
    wards = Ward.objects.filter(
        departments__id__in=department_ids).order_by(
        'position', 'name').prefetch_related('after_this')
    different_days = DifferentDay.objects.filter(
        ward__departments__id__in=department_ids,
        day__gte=start_of_data).select_related('ward')
    plannings = Planning.objects.filter(
        ward__in=wards,
        end__gte=start_of_data,
        superseded_by=None).select_related('ward')

    is_editor = session.get('is_editor', False)
    if not is_editor:
        plannings = [p for p in plannings
                     if not p.ward.approved or p.start <= p.ward.approved]
    holidays = get_holidays_for_company(session['company_id'])
    departments = dict(
        (d.id, d.name) for d in
        Department.objects.filter(id__in=department_ids))
    data = {
        'persons': [p.toJson() for p in persons_qs
                    if p.end_date >= start_of_data],
        'wards': [w.toJson() for w in wards if w.active],
        'different_days': [
            (dd.ward.shortname,
             dd.day.strftime('%Y%m%d'),
             '+' if dd.added else '-')
            for dd in different_days],
        'plannings': [p.toJson() for p in plannings],
        'is_editor': is_editor,
        'is_dep_lead': session.get('is_dep_lead', False),
        'is_company_admin': session.get('is_company_admin', False),
        'data_year': start_of_data.year,
        'data_month': start_of_data.month - 1,
        'holidays': [h.toJson() for h in holidays],
        'departments': departments,
    }
    last_change = ChangeLogging.objects.filter(
        company_id=session['company_id'],
    ).values('pk', 'change_time').order_by('pk').last()
    if last_change is not None:
        time_diff = datetime.now(pytz.utc) - last_change['change_time']
        data['last_change_pk'] = last_change['pk']
        data['last_change_time'] = time_diff.days * 86400 + time_diff.seconds

    return {
        'data': json.dumps(data),
        'former_persons': [p for p in persons_qs
                           if p.end_date < start_of_data],
        'inactive_wards': [w for w in wards if not w.active],
    }
