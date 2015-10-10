# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sp_app', '0006_auto_20150924_0433'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='shortname',
            field=models.CharField(max_length=10, verbose_name='Short Name', default='x'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='department',
            name='shortname',
            field=models.CharField(max_length=10, verbose_name='Short Name', default='x'),
            preserve_default=False,
        ),
    ]
