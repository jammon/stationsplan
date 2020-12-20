# -*- coding: utf-8 -*-
import datetime
from django import forms
from django.db import models
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .models import (Person, Ward, ChangeLogging, Planning, Department,
                     Company, Employee, StatusEntry, Holiday, CalculatedHoliday, Region,
                     DifferentDay)
from .forms import WardForm


class ConfigSite(admin.sites.AdminSite):
    """AdminSite for users"""
    site_header = "Konfiguration der Stationsplanung"
    site_title = "Konfiguration der Stationsplanung"
    site_url = '/plan'
    index_title = "Stationsplan Konfiguration"

    def has_permission(self, request):
        return request.session.get('is_dep_lead', False)


config_site = ConfigSite(name='config')


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
            kwargs["queryset"] = model_class.objects.filter(
                company_id=request.session.get('company_id'))
        return super(RestrictFields, self).formfield_for_foreignkey(
            db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        model_class = FIELDMODELS.get(db_field.name)
        if model_class:
            kwargs["queryset"] = model_class.objects.filter(
                company_id=request.session.get('company_id'))
        return super(RestrictFields, self).formfield_for_manytomany(
            db_field, request, **kwargs)


#
# Filters
#
class PersonWardListFilter(admin.SimpleListFilter):
    """ Return only models of the current Company and filter for
    self.parameter_name
    """
    def lookups(self, request, model_admin):
        return self.model.objects.filter(
            company_id=request.session.get('company_id')
        ).values_list('id', 'name')

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(**{
                f"{self.parameter_name}_id": int(value)})
        return queryset


class WardListFilter(PersonWardListFilter):
    title = _('Ward')
    parameter_name = 'ward'
    model = Ward


class PersonListFilter(PersonWardListFilter):
    title = _('Person')
    parameter_name = 'person'
    model = Person


class IsEmployedListFilter(admin.SimpleListFilter):
    """ Toggle if former employees are displayed
    """
    title = _('Anstellungsstatus')
    parameter_name = 'current'

    def lookups(self, request, model_admin):
        return (
            ('current', _('aktuelle Mitarbeiter')),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if self.value() == "current":
            return queryset.filter(end_date__gte=datetime.date.today())
        return queryset


class CurrentPersonListFilter(PersonListFilter):
    """Doesn't show former employees"""
    def lookups(self, request, model_admin):
        return self.model.objects.filter(
            company_id=request.session.get('company_id'),
            end_date__gte=datetime.date.today()
        ).values_list('id', 'name')


class DepartmentsListFilter(admin.SimpleListFilter):
    title = _('Department')
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


#
# Admins
#
@admin.register(Person)
@admin.register(Person, site=config_site)
class PersonAdmin(CompanyRestrictedMixin, RestrictFields, admin.ModelAdmin):
    # filter_horizontal = ('departments', 'functions',)
    list_filter = (IsEmployedListFilter, DepartmentsListFilter, )
    ordering = ('position', 'name',)
    list_display = ('name', 'shortname', 'position')
    list_editable = ('position',)
    formfield_overrides = {
        models.ManyToManyField: {
            'widget': forms.CheckboxSelectMultiple
        },
    }
    fields = (
        ('name', 'shortname'),
        ('start_date', 'end_date'),
        ('departments', 'functions'),
        ('position', 'anonymous'), )


class DifferentDayInline(admin.TabularInline):
    model = DifferentDay
    extra = 1


@admin.register(Ward)
@admin.register(Ward, site=config_site)
class WardAdmin(CompanyRestrictedMixin, RestrictFields, admin.ModelAdmin):
    form = WardForm
    fieldsets = (
        (None, {'fields': (
            (('name', 'shortname', 'position'),
             ('max', 'min', 'approved'),
             ('everyday', 'freedays', 'on_leave', 'callshift', ),
             ('weekdays', ),
             ('ward_type', 'weight',),
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
    inlines = [
        DifferentDayInline,
    ]


@admin.register(Department)
class DepartmentAdmin(CompanyRestrictedMixin, admin.ModelAdmin):
    ordering = ('shortname',)


class PersonDepartmentsListFilter(admin.SimpleListFilter):
    title = _('Department')
    parameter_name = 'departments'

    def lookups(self, request, model_admin):
        return Department.objects.filter(
            company_id=request.session.get('company_id')
        ).values_list('id', 'name')

    def queryset(self, request, queryset):
        qs = queryset.filter(company_id=request.session.get('company_id'))
        value = self.value()
        if value is not None:
            qs = qs.filter(person__departments__id=int(value))
        return qs


@admin.register(ChangeLogging)
class ChangeLoggingAdmin(admin.ModelAdmin):
    date_hierarchy = 'day'
    list_filter = (PersonDepartmentsListFilter,
                   CurrentPersonListFilter, WardListFilter,
                   'user', 'continued')
    list_display = ('description', 'change_time', )


@admin.register(Planning)
class PlanningAdmin(admin.ModelAdmin):
    date_hierarchy = 'start'
    list_filter = (PersonListFilter, WardListFilter)


@admin.register(StatusEntry)
class StatusEntryAdmin(CompanyRestrictedMixin, admin.ModelAdmin):
    list_display = ('name', 'content', 'department', 'company')


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    ordering = ('date', )


@admin.register(CalculatedHoliday)
class CalculatedHolidayAdmin(admin.ModelAdmin):
    ordering = ('name', )
    radio_fields = {"mode": admin.HORIZONTAL}
    fields = (('name', 'mode'), ('day', 'month', 'year'))


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    filter_horizontal = ('calc_holidays',)


admin.site.register(Company)
admin.site.register(Employee)
