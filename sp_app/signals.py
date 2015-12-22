from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver


@receiver(user_logged_in)
def write_department_id_to_session(sender, **kwargs):
    request = kwargs['request']
    user = kwargs['user']
    employee = user.employee
    request.session['company_id'] = employee.company_id
    request.session['department_ids'] = list(
        employee.departments.values_list('id', flat=True))
    request.session['can_config'] = user.has_perm('sp_app.add_person')
    # User with editing rights should have their sessions expired
    # when the browser is closed.
    if (user.has_perm('sp_app.add_changingstaff') or
        user.has_perm('sp_app.add_person')):
        request.session.set_expiry(0)
