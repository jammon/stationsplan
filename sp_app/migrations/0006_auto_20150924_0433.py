# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings

import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("sp_app", "0005_auto_20150922_0336"),
    ]

    operations = [
        migrations.CreateModel(
            name="Company",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        verbose_name="ID",
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("name", models.CharField(max_length=50, verbose_name="Name")),
            ],
            options={
                "verbose_name_plural": "Companies",
                "verbose_name": "Company",
            },
        ),
        migrations.CreateModel(
            name="Employee",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        verbose_name="ID",
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="employees",
                        to="sp_app.Company",
                    ),
                ),
            ],
        ),
        migrations.AlterField(
            model_name="changingstaff",
            name="person",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="sp_app.Person"
            ),
        ),
        migrations.AlterField(
            model_name="changingstaff",
            name="ward",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="sp_app.Ward"
            ),
        ),
        migrations.AlterField(
            model_name="department",
            name="company",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                help_text="The top organizational unit",
                related_name="departments",
                to="sp_app.Company",
            ),
        ),
        migrations.AlterField(
            model_name="person",
            name="department",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                null=True,
                related_name="persons",
                to="sp_app.Department",
            ),
        ),
        migrations.AlterField(
            model_name="ward",
            name="department",
            field=models.ManyToManyField(related_name="wards", to="sp_app.Department"),
        ),
        migrations.AddField(
            model_name="employee",
            name="department",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                null=True,
                related_name="employees",
                to="sp_app.Department",
            ),
        ),
        migrations.AddField(
            model_name="employee",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="employee",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="person",
            name="company",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                null=True,
                related_name="persons",
                to="sp_app.Company",
            ),
        ),
        migrations.AddField(
            model_name="ward",
            name="company",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                default=1,
                related_name="wards",
                to="sp_app.Company",
            ),
            preserve_default=False,
        ),
    ]
