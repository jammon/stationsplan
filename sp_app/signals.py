from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from .models import Ward, Employee


@receiver(user_logged_in)
def write_department_id_to_session(sender, **kwargs):
    request = kwargs['request']
    user = kwargs['user']
    try:
        employee = Employee.objects.get(user_id=user.id)
        request.session['company_id'] = employee.company_id
        request.session['department_ids'] = list(
            employee.departments.values_list('id', flat=True))
    except Employee.DoesNotExist:
        pass
    request.session['user_name'] = user.get_full_name() or user.get_username()
    request.session['is_dep_lead'] = user.has_perm('sp_app.add_person')
    # User with editing rights should have their sessions expired
    # when the browser is closed.
    # They can change their passwords
    if (user.has_perm('sp_app.add_changelogging') or
            request.session['is_dep_lead']):
        request.session.set_expiry(0)
        request.session['is_editor'] = True
        request.session['can_change_password'] = True
