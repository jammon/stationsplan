# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
from django.db import migrations, models


def toJson(ward):
    return {'name': ward.name,
            'shortname': ward.shortname,
            'min': ward.min,
            'max': ward.max,
            'nightshift': ward.nightshift,
            'everyday': ward.everyday,
            'freedays': ward.freedays,
            'continued': ward.continued,
            'on_leave': ward.on_leave,
            'company_id': ward.company_id,
            'position': ward.position,
            'approved': date_to_json(ward.approved) if ward.approved else None,
            'id': ward.id,
            'after_this': '' if not ward.pk else ','.join(
                ward.after_this.values_list('shortname', flat=True)),
            }

def save_json(apps, schema_editor):
    Ward = apps.get_model("sp_app", "Ward")
    for ward in Ward.objects.all():
        ward.json = json.dumps(toJson(ward))
        ward.save()

class Migration(migrations.Migration):

    dependencies = [
        ('sp_app', '0025_ward_json'),
    ]

    operations = [
    	migrations.RunPython(save_json),
    ]
