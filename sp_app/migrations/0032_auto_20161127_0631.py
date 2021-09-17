# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("sp_app", "0031_auto_20160820_0510"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="changelogging",
            options={
                "verbose_name": "\xc4nderung",
                "verbose_name_plural": "\xc4nderungen",
            },
        ),
        migrations.AlterModelOptions(
            name="employee",
            options={
                "verbose_name": "Bearbeiter",
                "verbose_name_plural": "Bearbeiter",
            },
        ),
        migrations.AlterModelOptions(
            name="planning",
            options={
                "verbose_name": "Planung",
                "verbose_name_plural": "Planungen",
            },
        ),
        migrations.AddField(
            model_name="planning",
            name="superseded_by",
            field=models.ForeignKey(
                related_name="supersedes",
                on_delete=django.db.models.deletion.SET_NULL,
                default=None,
                blank=True,
                to="sp_app.Planning",
                help_text="Later planning that supersedes this one",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="person",
            name="anonymous",
            field=models.BooleanField(
                default=False,
                help_text="wenn Wahr, dann steht diese Person f\xfcr mehrere andere Personen, z.B. eine Abteilung",
                verbose_name="Anonym",
            ),
        ),
        migrations.AlterField(
            model_name="statusentry",
            name="company",
            field=models.ForeignKey(
                related_name="status_entries",
                on_delete=django.db.models.deletion.CASCADE,
                blank=True,
                to="sp_app.Company",
                help_text="Kann leer bleiben",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="statusentry",
            name="department",
            field=models.ForeignKey(
                related_name="status_entries",
                on_delete=django.db.models.deletion.CASCADE,
                blank=True,
                to="sp_app.Department",
                help_text="Kann leer bleiben",
                null=True,
            ),
        ),
    ]
