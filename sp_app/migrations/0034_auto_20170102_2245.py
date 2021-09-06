# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("sp_app", "0033_changelogging_until"),
    ]

    operations = [
        migrations.CreateModel(
            name="WardType",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("name", models.CharField(max_length=20, verbose_name="Name")),
                ("callshift", models.BooleanField(verbose_name="Call shift")),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ward_types",
                        to="sp_app.Company",
                    ),
                ),
            ],
        ),
        migrations.AlterField(
            model_name="changelogging",
            name="continued",
            field=models.BooleanField(
                default=True, help_text="If False the change is valid for one day."
            ),
        ),
        migrations.AlterField(
            model_name="changelogging",
            name="until",
            field=models.DateField(
                help_text="The last day the change is valid. Can be blank.",
                null=True,
                blank=True,
            ),
        ),
        migrations.AddField(
            model_name="ward",
            name="ward_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="wards",
                default=None,
                to="sp_app.WardType",
                null=True,
            ),
        ),
    ]
