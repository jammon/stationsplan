# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
from django.db import migrations, models

def update_changelogging(apps, schema_editor):
    ChangeLogging = apps.get_model("sp_app", "ChangeLogging")
    template = (
        "{user_name}: {self.person.name} ist {relation} {date} für "
        "{self.ward.name} {added}eingeteilt")
    for cl in ChangeLogging.objects.all().select_related('person', 'ward', 'user'):
    	cl.json = json.dumps({
            'person': cl.person.shortname,
            'ward': cl.ward.shortname,
            'day': cl.day.strftime('%Y%m%d'),
            'action': 'add' if cl.added else 'remove',
        })
        cl.description = template.format(
            user_name=cl.user.last_name or cl.user.username,
            self=cl,
            relation="ab" if cl.ward.continued else "am",
            date=cl.day.strftime('%Y-%m-%d'),
            added="" if cl.added else "nicht mehr ")
        cl.save()

class Migration(migrations.Migration):

    dependencies = [
        ('sp_app', '0021_auto_20151229_0608'),
    ]

    operations = [
        migrations.RunPython(update_changelogging),
    ]
