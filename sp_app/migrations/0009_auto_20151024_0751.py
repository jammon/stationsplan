# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def copy_departments(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Person = apps.get_model("sp_app", "Person")
    for person in Person.objects.all():
        if person.department:
            person.departments.add(person.department)
    Employee = apps.get_model("sp_app", "Employee")
    for employee in Employee.objects.all():
        if employee.department:
            employee.departments.add(employee.department)


class Migration(migrations.Migration):

    dependencies = [
        ("sp_app", "0008_auto_20151024_0750"),
    ]

    operations = [
        migrations.RunPython(copy_departments),
    ]
