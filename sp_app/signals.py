from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .models import Employee


@receiver(user_logged_in)
def write_department_id_to_session(sender, **kwargs):
    request = kwargs["request"]
    user = kwargs["user"]
    try:
        employee = Employee.objects.get(user_id=user.id)
        request.session["company_id"] = employee.company_id
        request.session["department_ids"] = list(
            employee.departments.values_list("id", flat=True)
        )
    except Employee.DoesNotExist:
        pass
    request.session["user_name"] = user.get_full_name() or user.get_username()
    editors = ("is_editor", "is_dep_lead", "is_company_admin")
    for perm in editors:
        request.session[perm] = user.has_perm("sp_app." + perm)
    # User with editing rights should have their sessions expired
    # when the browser is closed.
    # They can change their passwords
    for perm in editors:
        if request.session[perm]:
            request.session.set_expiry(0)
            request.session["can_change_password"] = True
            break
