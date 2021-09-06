# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sp_app", "0026_auto_20160108_2132"),
    ]

    operations = [
        migrations.AddField(
            model_name="changelogging",
            name="continued",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="changelogging",
            name="version",
            field=models.IntegerField(default=0),
        ),
    ]
