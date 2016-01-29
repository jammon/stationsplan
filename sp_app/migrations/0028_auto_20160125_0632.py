# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def save_continued(apps, schema_editor):
    ChangeLogging = apps.get_model("sp_app", "ChangeLogging")
    for cl in ChangeLogging.objects.all().select_related('ward'):
        cl.continued = cl.ward.continued
        cl.save()


class Migration(migrations.Migration):

    dependencies = [
        ('sp_app', '0027_auto_20160121_1908'),
    ]

    operations = [
        migrations.RunPython(save_continued),
    ]
