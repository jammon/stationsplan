# Generated by Django 3.1.5 on 2021-05-26 08:39

from django.db import migrations


PERMISSIONS = (
    ('Editors', 'is_editor'),
    ('Department admins', 'is_dep_lead'),
    ('Company Admin', 'is_company_admin'),
)


def migrate_permissions(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    for g, p in PERMISSIONS:
        try:
            group = Group.objects.get(name=g)
            permission = Permission.objects.get(codename=p)
            group.permissions.add(permission)
        except Group.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('sp_app', '0053_auto_20210526_0805'),
    ]

    operations = [
        migrations.RunPython(migrate_permissions),
    ]