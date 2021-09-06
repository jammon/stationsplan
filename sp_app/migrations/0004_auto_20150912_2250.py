# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ("sp_app", "0003_auto_20150912_1701"),
    ]

    operations = [
        migrations.AlterField(
            model_name="person",
            name="end_date",
            field=models.DateField(
                help_text="end of job", default=datetime.date(2099, 12, 31)
            ),
        ),
        migrations.AlterField(
            model_name="person",
            name="start_date",
            field=models.DateField(
                help_text="begin of job", default=datetime.date(2015, 1, 1)
            ),
        ),
    ]
