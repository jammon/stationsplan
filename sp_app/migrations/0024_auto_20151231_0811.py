# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sp_app", "0023_changelogging_change_time"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="changingstaff",
            name="person",
        ),
        migrations.RemoveField(
            model_name="changingstaff",
            name="ward",
        ),
        migrations.AlterField(
            model_name="changelogging",
            name="change_time",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.DeleteModel(
            name="ChangingStaff",
        ),
    ]
