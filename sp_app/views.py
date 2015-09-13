from datetime import datetime, date, timedelta
from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import render
import json

from .models import Person, Ward, ChangingStaff


def get_past_changes(first_of_month):
    past_changes = set()
    for c in ChangingStaff.objects.filter(
        day__gt=first_of_month-timedelta(days=92),  # three months back
        day__lt=first_of_month
    ).order_by('day'):
        if c.added:
            past_changes.add((c.person, c.ward))
        else:
            past_changes.discard((c.person, c.ward))
    return [ChangingStaff(person=person, ward=ward,
                          day=first_of_month, added=True).toJson()
            for person, ward in past_changes]


def last_day_of_month(date):
    return (date.replace(day=31)
            if date.month == 12
            else date.replace(month=date.month+1, day=1) - timedelta(days=1))


def changes_for_month(first_of_month):
    last_of_month = last_day_of_month(first_of_month)

    past_changes = get_past_changes(first_of_month)
    current_changes = [c.toJson() for c in ChangingStaff.objects.filter(
        day__gte=first_of_month,
        day__lt=last_of_month
    ).order_by('day')]
    return past_changes + current_changes


def home(request):
    first_of_month = date.today().replace(day=1)
    persons = [p.toJson() for p in Person.objects.filter(
        start_date__lt=first_of_month.replace(year=first_of_month.year+1,
                                              month=12, day=31),
        end_date__gt=first_of_month.replace(month=1))]
    data = {
        'persons': json.dumps(persons),
        'wards': json.dumps(list(Ward.objects.values())),
        'past_changes': json.dumps(get_past_changes(first_of_month)),
        'changes': json.dumps(changes_for_month(first_of_month)),
        'year': first_of_month.year,
        'month': first_of_month.month,
    }
    return render(request, 'sp_app/index.html', data)


def month(request, year, month):
    data = changes_for_month(date(int(year), int(month), 1))
    return JsonResponse(data)


def tests(request):
    return render(request, 'sp_app/tests.html', {})


def change(request):
    """One *person* is
    added to or removed (*action*)
    on one *day*
    from the staffing of one *ward*
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    person = request.POST['person']
    ward = request.POST['ward']
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
