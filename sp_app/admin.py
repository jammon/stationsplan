# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib import admin

from .models import (Person, Ward, ChangingStaff, ChangeLogging, Department,
                     Company, Employee)
from .forms import WardForm


class CompanyRestrictedMixin(object):
    """ Limits access to objects, that have their "company" field set
    to the users company.
    """
    # readonly_fields = ('company',)  # just for testing
    exclude = ('company',)

    def save_model(self, request, obj, form, change):
        obj.company_id = request.session.get('company_id')
        obj.save()

    def get_queryset(self, request):
        qs = super(CompanyRestrictedMixin, self).get_queryset(request)
        return qs.filter(company_id=request.session.get('company_id'))


FIELDMODELS = {
    'person': Person,
    'ward': Ward,
    'functions': Ward,
    'departments': Department,
}


class RestrictFields(object):
    """ Limits access of ForeignKeys or ManyToMany-Fields to objects
    belonging to the company stored in the session.
    """

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        model_class = FIELDMODELS.get(db_field.name)
        if model_class:
            print db_field.name
            kwargs["queryset"] = model_class.objects.filter(
                company_id=request.session.get('company_id'))
        return super(RestrictFields, self).formfield_for_foreignkey(
            db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        model_class = FIELDMODELS.get(db_field.name)
        if model_class:
            print db_field.name
            kwargs["queryset"] = model_class.objects.filter(
                company_id=request.session.get('company_id'))
        return super(RestrictFields, self).formfield_for_manytomany(
            db_field, request, **kwargs)


class ChangingStaffAdmin(CompanyRestrictedMixin, RestrictFields, admin.ModelAdmin):
    date_hierarchy = 'day'


class PersonAdmin(CompanyRestrictedMixin, RestrictFields, admin.ModelAdmin):
    filter_horizontal = ('departments', 'functions',)
    list_filter = ('departments', )
    ordering = ('position', 'name',)
    list_display = ('name', 'position')
    list_editable = ('position',)


class WardAdmin(CompanyRestrictedMixin, RestrictFields, admin.ModelAdmin):
    form = WardForm
    fieldsets = (
        (None, {'fields': (
            (('name', 'shortname', 'position'),
             ('max', 'min', 'approved'),
             ('nightshift', 'everyday', 'freedays', 'continued', 'on_leave',),
             'departments', 'staff'))
        }),
    )
    filter_horizontal = ('departments', )
    list_filter = ('departments', )
    ordering = ('position', 'name',)
    list_display = ('name', 'shortname', 'position')
    list_editable = ('position',)


class DepartmentAdmin(CompanyRestrictedMixin, admin.ModelAdmin):
    pass


admin.site.register(ChangingStaff, ChangingStaffAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Ward, WardAdmin)

admin.site.register(Department)
admin.site.register(Company)
admin.site.register(Employee)
admin.site.register(ChangeLogging)


class ConfigSite(admin.sites.AdminSite):
    """AdminSite for users"""
    site_header = "Konfiguration der Stationsplanung"
    site_title = "Konfiguration der Stationsplanung"
    site_url = '/plan'
    index_title = "Stationsplan Konfiguration"

    def has_permission(self, request):
        return request.session.get('can_config', False)


config_site = ConfigSite(name='config')


config_site.register(Department, DepartmentAdmin)
config_site.register(Ward, WardAdmin)
config_site.register(Person, PersonAdmin)
