# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sp_app', '0030_auto_20160307_0627'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='changelogging',
            options={},
        ),
        migrations.AddField(
            model_name='person',
            name='anonymous',
            field=models.BooleanField(default=False, help_text='if True this person represents multiple other persons, e.g. an appartment', verbose_name='Anonymous'),
        ),
    ]
