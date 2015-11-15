# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sp_app', '0015_auto_20151112_1559'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ward',
            options={'verbose_name': 'Task', 'verbose_name_plural': 'Tasks'},
        ),
        migrations.AddField(
            model_name='ward',
            name='approved',
            field=models.DateField(null=True, blank=True),
        ),
    ]
