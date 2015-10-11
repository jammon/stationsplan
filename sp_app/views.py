from __future__ import unicode_literals
import json
from datetime import datetime, date
from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.generic.base import TemplateView
from django.contrib.auth.decorators import login_required

from .models import Person, Ward, ChangingStaff, Department
from .utils import get_past_changes, changes_for_month


class HomePageView(TemplateView):
    template_name = "sp_app/index.html"


@login_required
def plan(request):
    department = get_object_or_404(
        Department, id=request.session.get('department_id'))
    first_of_month = date.today().replace(day=1)
    persons = [p.toJson() for p in Person.objects.filter(
        start_date__lt=first_of_month.replace(year=first_of_month.year+1,
                                              month=12, day=31),
        end_date__gt=first_of_month.replace(month=1),
        department=department)]
    wards = Ward.objects.filter(department=department)
    name = request.user.get_full_name() or request.user.get_username()
    data = {
        'persons': json.dumps(persons),
        'wards': json.dumps(list(wards.values())),
        'past_changes': json.dumps(get_past_changes(first_of_month, wards)),
        'changes': json.dumps(changes_for_month(first_of_month, wards)),
        'year': first_of_month.year,
        'month': first_of_month.month,
        'user': request.user,
        'name': name,
        'can_change': 1 if request.user.has_perm('sp_app.add_changingstaff') else 0,
    }
    return render(request, 'sp_app/plan.html', data)


@login_required
def month(request):
    department_id = request.session.get('department_id')
    wards = Ward.objects.filter(department__id=department_id)
    year = request.GET['year']
    month = request.GET['month']
    data = changes_for_month(date(int(year), int(month), 1), wards)
    # data['can_change'] = request.user.has_perm('sp_app.add_changingstaff')
    return JsonResponse(data, safe=False)


def tests(request):
    return render(request, 'sp_app/tests.html', {})


@login_required
def change(request):
    """One *person* is
    added to or removed (*action*)
    on one *day*
    from the staffing of one *ward*
    """
    print("change requested")
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    person = get_object_or_404(Person, shortname=request.POST['person'])
    ward = get_object_or_404(Ward, shortname=request.POST['ward'])
    day = datetime.strptime(request.POST['day'], '%Y%m%d').date()
    added = request.POST['action'] == 'add'
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
