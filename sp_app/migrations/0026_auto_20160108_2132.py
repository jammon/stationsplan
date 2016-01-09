# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
from django.db import migrations, models


def save_json(apps, schema_editor):
    Ward = apps.get_model("sp_app", "Ward")
    for ward in Ward.objects.all():
        ward.json = json.dumps(ward.toJson())
        ward.save()

class Migration(migrations.Migration):

    dependencies = [
        ('sp_app', '0025_ward_json'),
    ]

    operations = [
    	migrations.RunPython(save_json),
    ]
