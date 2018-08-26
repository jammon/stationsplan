# Generated by Django 2.0 on 2018-08-10 13:03

import json
from django.db import migrations


def get_callshift(apps, schema_editor):
    # We can't import the Ward model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Ward = apps.get_model("sp_app", "Ward")
    for ward in Ward.objects.all():
        ward.callshift = '"continued": false' in ward.json
        # ward.json = json.dumps(ward.toJson())
        ward.save()


class Migration(migrations.Migration):

    dependencies = [
        ('sp_app', '0043_auto_20180810_1501'),
    ]

    operations = [
        migrations.RunPython(get_callshift),
    ]
