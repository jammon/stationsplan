# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-28 09:29
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sp_app', '0037_auto_20170521_1301'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='holiday',
            options={'verbose_name': 'Feiertag', 'verbose_name_plural': 'Feiertage'},
        ),
        migrations.AlterModelOptions(
            name='region',
            options={'verbose_name': 'Region', 'verbose_name_plural': 'Regionen'},
        ),
        migrations.AlterField(
            model_name='company',
            name='extra_holidays',
            field=models.ManyToManyField(blank=True, related_name='companies', to='sp_app.Holiday', verbose_name='Zus\xe4tzliche Feiertage'),
        ),
        migrations.AlterField(
            model_name='company',
            name='region',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='companies', to='sp_app.Region'),
        ),
    ]
