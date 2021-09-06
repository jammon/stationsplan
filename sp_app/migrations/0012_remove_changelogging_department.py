# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sp_app", "0011_changelogging"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="changelogging",
            name="department",
        ),
    ]
