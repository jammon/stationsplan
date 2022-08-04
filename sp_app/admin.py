# -*- coding: utf-8 -*-
import datetime
from django import forms
from django.db import models
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    Person,
    Ward,
    ChangeLogging,
    Planning,
    Department,
    Company,
    Employee,
    StatusEntry,
    CalculatedHoliday,
    Region,
    DifferentDay,
)
from .forms import WardAdminForm


class ConfigSite(admin.sites.AdminSite):
    """AdminSite for users"""

    site_header = "Konfiguration der Stationsplanung"
    site_title = "Konfiguration der Stationsplanung"
    site_url = "/plan"
    index_title = "Stationsplan Konfiguration"

    def has_permission(self, request):
        return request.session.get("is_dep_lead", False)


config_site = ConfigSite(name="config")


FIELDMODELS = {
    "person": Person,
    "ward": Ward,
    "functions": Ward,
    "departments": Department,
    "after_this": Ward,
    "not_with_this": Ward,
}


#
# Filters
#
class IsEmployedListFilter(admin.SimpleListFilter):
    """Toggle if former employees are displayed"""

    title = _("Employment status")
    parameter_name = "current"

    def lookups(self, request, model_admin):
        return (("current", _("current employees")),)

    def queryset(self, request, queryset):
        if self.value() == "current":
            return queryset.filter(end_date__gte=datetime.date.today())
        return queryset


#
# Admins
#
@admin.register(Person)
@admin.register(Person, site=config_site)
class PersonAdmin(admin.ModelAdmin):
    list_filter = ("company", IsEmployedListFilter, "departments")
    ordering = ("position", "name")
    list_display = ("name", "shortname", "position")
    list_editable = ("position",)
    formfield_overrides = {
        models.ManyToManyField: {"widget": forms.CheckboxSelectMultiple},
    }
    fieldsets = (
        (
            None,
            {
                "fields": (
                    (
                        ("name", "shortname"),
                        ("start_date", "end_date"),
                        ("departments", "functions"),
                    )
                )
            },
        ),
        (
            "Advanced options",
            {
                "classes": ("collapse",),
                "fields": (
                    "position",
                    "anonymous",
                ),
            },
        ),
    )


@admin.register(Ward)
@admin.register(Ward, site=config_site)
class WardAdmin(admin.ModelAdmin):
    form = WardAdminForm
    fieldsets = (
        (
            None,
            {
                "fields": (
                    (
                        ("name", "shortname", "position"),
                        ("max", "min", "approved"),
                        ("everyday", "freedays"),
                        ("on_leave", "callshift"),
                        "active",
                        "departments",
                        "staff",
                    )
                )
            },
        ),
        (
            "Advanced options",
            {
                "classes": ("collapse",),
                "fields": (
                    "weekdays",
                    (
                        "ward_type",
                        "weight",
                    ),
                    "after_this",
                    "not_with_this",
                ),
            },
        ),
    )
    filter_horizontal = ("departments", "after_this", "not_with_this")
    list_filter = ("company", "departments")
    ordering = ("position", "name")
    list_display = ("name", "shortname", "position")
    list_editable = ("position",)

    class DifferentDayInline(admin.TabularInline):
        model = DifferentDay
        extra = 1

    inlines = [
        DifferentDayInline,
    ]


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    ordering = ("shortname",)
    list_filter = ("company",)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    class DepartmentInline(admin.TabularInline):
        model = Department

    class EmployeeInline(admin.TabularInline):
        model = Employee

        def formfield_for_manytomany(self, db_field, request, **kwargs):
            if db_field.name == "departments":
                kwargs["queryset"] = request.department_qs
            return super().formfield_for_manytomany(
                db_field, request, **kwargs
            )

    inlines = DepartmentInline, EmployeeInline

    def get_form(self, request, obj=None, **kwargs):
        # just save querysets reference for future processing in Inline
        if obj is not None:
            request.department_qs = Department.objects.filter(company=obj)
        return super().get_form(request, obj, **kwargs)


@admin.register(ChangeLogging)
class ChangeLoggingAdmin(admin.ModelAdmin):
    date_hierarchy = "day"
    list_filter = (
        "company",
        "person",
        "ward",
        "user",
        "continued",
    )
    list_display = ("description", "change_time")


@admin.register(Planning)
class PlanningAdmin(admin.ModelAdmin):
    date_hierarchy = "start"
    list_filter = ("company", "person", "ward")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("person", "ward")


@admin.register(StatusEntry)
class StatusEntryAdmin(admin.ModelAdmin):
    list_display = ("name", "content", "department", "company")
    list_filter = ("company",)


@admin.register(CalculatedHoliday)
class CalculatedHolidayAdmin(admin.ModelAdmin):
    ordering = ("name",)
    radio_fields = {"mode": admin.HORIZONTAL}
    fields = (("name", "mode"), ("day", "month", "year"))


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    filter_horizontal = ("calc_holidays",)
