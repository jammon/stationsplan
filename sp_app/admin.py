# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .models import (Person, Ward, ChangeLogging, Planning, Department,
                     Company, Employee, StatusEntry, WardType)
from .forms import WardForm


class CompanyRestrictedMixin(object):
    """ Limits access to objects, that have their "company" field set
    to the users company.
    """
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


class PersonWardListFilter(admin.SimpleListFilter):

    def lookups(self, request, model_admin):
        return self.model.objects.filter(
            company_id=request.session.get('company_id')
        ).values_list('id', 'name')

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(**{
                "{}_id".format(self.parameter_name): int(value)})
        return queryset


class WardListFilter(PersonWardListFilter):
    title = _('Ward')
    parameter_name = 'ward'
    model = Ward


class PersonListFilter(PersonWardListFilter):
    title = _('Person')
    parameter_name = 'person'
    model = Person


class DepartmentsListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('Department')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'departments'

    def lookups(self, request, model_admin):
        return Department.objects.filter(
            company_id=request.session.get('company_id')
        ).values_list('id', 'name')

    def queryset(self, request, queryset):
        qs = queryset.filter(company_id=request.session.get('company_id'))
        value = self.value()
        if value is not None:
            qs = qs.filter(departments__id=int(value))
        return qs


class PersonAdmin(CompanyRestrictedMixin, RestrictFields, admin.ModelAdmin):
    filter_horizontal = ('departments', 'functions',)
    list_filter = (DepartmentsListFilter, )
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
             'ward_type',
             'departments',
             'staff',
             'after_this',
             ))
        }),
    )
    filter_horizontal = ('departments', 'after_this')
    list_filter = (DepartmentsListFilter, )
    ordering = ('position', 'name',)
    list_display = ('name', 'shortname', 'position')
    list_editable = ('position',)


class DepartmentAdmin(CompanyRestrictedMixin, admin.ModelAdmin):
    pass


class ChangeLoggingAdmin(admin.ModelAdmin):
    date_hierarchy = 'day'
    list_filter = (DepartmentsListFilter, PersonListFilter, WardListFilter,
                   'continued')


class PlanningAdmin(admin.ModelAdmin):
    date_hierarchy = 'start'
    list_filter = (PersonListFilter, WardListFilter)


class WardTypeAdmin(admin.ModelAdmin):
    fields = ('name', 'callshift', 'company', )


class StatusEntryAdmin(CompanyRestrictedMixin, admin.ModelAdmin):
    list_display = ('name', 'content', 'department', 'company')


admin.site.register(Person, PersonAdmin)
admin.site.register(Ward, WardAdmin)
admin.site.register(Department)
admin.site.register(Company)
admin.site.register(Employee)
admin.site.register(ChangeLogging, ChangeLoggingAdmin)
admin.site.register(Planning, PlanningAdmin)
admin.site.register(StatusEntry, StatusEntryAdmin)
admin.site.register(WardType, WardTypeAdmin)


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
config_site.register(WardType)
