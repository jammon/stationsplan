# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from sp_app import models


def apply_plannings(apps, schema_editor):
    ChangeLogging = apps.get_model("sp_app", "ChangeLogging")
    for cl in ChangeLogging.objects.all().select_related("person", "ward"):
        models.process_change(cl)


class Migration(migrations.Migration):

    dependencies = [
        ("sp_app", "0029_planning"),
    ]

    operations = [
        migrations.RunPython(apply_plannings),
    ]
