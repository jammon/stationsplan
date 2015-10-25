from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver


@receiver(user_logged_in)
def write_department_id_to_session(sender, **kwargs):
    request = kwargs['request']
    employee = kwargs['user'].employee
    request.session['company_id'] = employee.company_id
    request.session['department_ids'] = list(
        employee.departments.values_list('id', flat=True))
