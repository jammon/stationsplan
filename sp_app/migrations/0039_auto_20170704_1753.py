# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-04 15:53
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("sp_app", "0038_auto_20170528_1129"),
    ]

    operations = [
        migrations.AddField(
            model_name="ward",
            name="weight",
            field=models.IntegerField(
                default=0,
                help_text="if this is a call shift, the weight reflects its burden on the persons doing the shift",
            ),
        ),
        migrations.AlterField(
            model_name="company",
            name="region",
            field=models.ForeignKey(
                blank=True,
                help_text="Region (Bundesland), deren Feiertage f\xfcr dieses Krankenhaus gelten.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="companies",
                to="sp_app.Region",
            ),
        ),
        migrations.AlterField(
            model_name="region",
            name="holidays",
            field=models.ManyToManyField(
                related_name="regions", to="sp_app.Holiday", verbose_name="Feiertage"
            ),
        ),
        migrations.AlterField(
            model_name="ward",
            name="ward_type",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Zum Sortieren der Dienstbelastungen",
                max_length=50,
                verbose_name="Funktionsart",
            ),
        ),
    ]
