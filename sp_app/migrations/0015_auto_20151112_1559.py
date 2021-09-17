# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sp_app", "0014_person_functions"),
    ]

    operations = [
        migrations.AddField(
            model_name="person",
            name="position",
            field=models.IntegerField(
                default=1, help_text="Ordering in the display"
            ),
        ),
        migrations.AddField(
            model_name="ward",
            name="position",
            field=models.IntegerField(
                default=1, help_text="Ordering in the display"
            ),
        ),
        migrations.AlterField(
            model_name="person",
            name="functions",
            field=models.ManyToManyField(
                help_text="Functions that he or she can  perform.",
                related_name="staff",
                to="sp_app.Ward",
            ),
        ),
    ]
