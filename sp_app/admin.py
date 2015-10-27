from django.contrib import admin

from .models import (Person, Ward, ChangingStaff, ChangeLogging, Department,
                     Company, Employee)


class CompanyRestrictedAdmin(admin.ModelAdmin):
    """ Limits access to objects, that have their "company" field set
    to the users company.
    Prevents usual adding of objects, this has to be done via
    an inline-admin.
    """
    def queryset(self, request):
        qs = super(CompanyRestrictedAdmin, self).queryset(request)
        return qs.filter(company_id=request.session.get('company_id'))

    def has_add_permission(self, request):
        return False


class DepartmentRestrictedAdmin(CompanyRestrictedAdmin):
    """ Limits access to objects, that have their "departments" field set
    to the users departments.
    """
    def queryset(self, request):
        qs = super(DepartmentRestrictedAdmin, self).queryset(request)
        return qs.filter(
            departments_id__in=request.session.get('department_ids'))


@admin.register(ChangingStaff)
class ChangingStaffAdmin(DepartmentRestrictedAdmin):
    date_hierarchy = 'day'


admin.site.register(Person)
admin.site.register(Ward)
admin.site.register(Department)
admin.site.register(Company)
admin.site.register(Employee)
admin.site.register(ChangeLogging)
