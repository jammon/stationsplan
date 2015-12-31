# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('sp_app', '0022_auto_20151229_0610'),
    ]

    operations = [
        migrations.AddField(
            model_name='changelogging',
            name='change_time',
            field=models.DateTimeField(default=datetime.datetime(2015, 12, 29, 6, 23, 4, 673720, tzinfo=utc)),
            preserve_default=False,
        ),
    ]
