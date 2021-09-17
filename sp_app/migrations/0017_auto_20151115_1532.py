# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sp_app", "0016_auto_20151113_1444"),
    ]

    operations = [
        migrations.AddField(
            model_name="ward",
            name="freedays",
            field=models.BooleanField(
                default=False,
                help_text="if True, is to be planned only on free days.",
            ),
        ),
        migrations.AlterField(
            model_name="ward",
            name="approved",
            field=models.DateField(
                help_text="The date until which the plan is approved",
                null=True,
                blank=True,
            ),
        ),
    ]
