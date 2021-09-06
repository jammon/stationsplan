# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sp_app", "0024_auto_20151231_0811"),
    ]

    operations = [
        migrations.AddField(
            model_name="ward",
            name="json",
            field=models.CharField(default="", max_length=511),
            preserve_default=False,
        ),
    ]
