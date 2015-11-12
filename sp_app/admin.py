from django import forms
from django.contrib import admin

from .models import (Person, Ward, ChangingStaff, ChangeLogging, Department,
                     Company, Employee)
from .forms import WardForm


class CompanyRestrictedMixin(object):
    """ Limits access to objects, that have their "company" field set
    to the users company.
    Prevents usual adding of objects, this has to be done via
    an inline-admin.
    """
    readonly_fields = ('company',)  # just for testing
    # exclude = ('company',)

    def save_model(self, request, obj, form, change):
        obj.company_id = request.session.get('company_id')
        obj.save()

    def queryset(self, request):
        qs = super(CompanyRestrictedMixin, self).queryset(request)
        return qs.filter(company_id=request.session.get('company_id'))


class DepartmentRestrictedAdmin(admin.ModelAdmin):
    """ Limits access to objects, that have their "departments" field set
    to the users departments.
    """
    def queryset(self, request):
        qs = super(DepartmentRestrictedAdmin, self).queryset(request)
        return qs.filter(
            departments__id__in=request.session.get('department_ids'))


@admin.register(ChangingStaff)
class ChangingStaffAdmin(DepartmentRestrictedAdmin):
    date_hierarchy = 'day'


@admin.register(Person)
class PersonAdmin(CompanyRestrictedMixin, DepartmentRestrictedAdmin):
    filter_horizontal = ('departments', 'functions',)
    list_filter = ('departments', )
    ordering = ('name',)


@admin.register(Ward)
class WardAdmin(CompanyRestrictedMixin, DepartmentRestrictedAdmin):
    form = WardForm
    fieldsets = (
        (None, {'fields': (
            ('name', 'shortname',
             ('max', 'min'),
             ('nightshift', 'everyday', 'continued', 'on_leave',),
             'departments', 'company', 'staff'))
        }),
    )
    filter_horizontal = ('departments', )
    list_filter = ('departments', )
    ordering = ('name',)

admin.site.register(Department)
admin.site.register(Company)
admin.site.register(Employee)
admin.site.register(ChangeLogging)
