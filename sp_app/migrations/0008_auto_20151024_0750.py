# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sp_app', '0007_auto_20150924_0439'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='departments',
            field=models.ManyToManyField(related_name='employees', to='sp_app.Department'),
        ),
        migrations.AddField(
            model_name='person',
            name='departments',
            field=models.ManyToManyField(related_name='persons', to='sp_app.Department'),
        ),
        migrations.AlterField(
            model_name='employee',
            name='department',
            field=models.ForeignKey(related_name='employee', to='sp_app.Department', null=True),
        ),
        migrations.AlterField(
            model_name='person',
            name='department',
            field=models.ForeignKey(related_name='person', to='sp_app.Department', null=True),
        ),
    ]
