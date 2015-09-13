# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sp_app', '0002_changingstaff'),
    ]

    operations = [
        migrations.AlterField(
            model_name='changingstaff',
            name='person',
            field=models.CharField(verbose_name='Person', max_length=10),
        ),
        migrations.AlterField(
            model_name='changingstaff',
            name='ward',
            field=models.CharField(verbose_name='Ward', max_length=10),
        ),
    ]
