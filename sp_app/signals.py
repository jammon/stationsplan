from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver


@receiver(user_logged_in)
def write_department_id_to_session(sender, **kwargs):
    request = kwargs['request']
    user = kwargs['user']
    request.session['department_id'] = user.employee.department_id
