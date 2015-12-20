# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sp_app', '0018_auto_20151123_2254'),
    ]

    operations = [
        migrations.AddField(
            model_name='ward',
            name='after_this',
            field=models.ManyToManyField(help_text='if not empty, only these functions can be planned on the next day', to='sp_app.Ward'),
        ),
    ]
