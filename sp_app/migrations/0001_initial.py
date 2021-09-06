# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Person",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                ("name", models.CharField(verbose_name="Name", max_length=50)),
                (
                    "shortname",
                    models.CharField(verbose_name="Short Name", max_length=10),
                ),
                (
                    "start_date",
                    models.DateField(blank=True, help_text="begin of job", null=True),
                ),
                (
                    "end_date",
                    models.DateField(blank=True, help_text="end of job", null=True),
                ),
            ],
            options={
                "verbose_name": "Person",
                "verbose_name_plural": "Persons",
            },
        ),
        migrations.CreateModel(
            name="Ward",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                ("name", models.CharField(verbose_name="Name", max_length=50)),
                (
                    "shortname",
                    models.CharField(verbose_name="Short Name", max_length=10),
                ),
                ("max", models.IntegerField(help_text="maximum staffing")),
                ("min", models.IntegerField(help_text="minimum staffing")),
                (
                    "nightshift",
                    models.BooleanField(
                        help_text="if True, staffing can not be planned on the next day.",
                        default=False,
                    ),
                ),
                (
                    "everyday",
                    models.BooleanField(
                        help_text="if True, is to be planned also on free days.",
                        default=False,
                    ),
                ),
                (
                    "continued",
                    models.BooleanField(
                        help_text="if True, then todays staffing will be planned for tomorrow",
                        default=True,
                    ),
                ),
                (
                    "on_leave",
                    models.BooleanField(
                        help_text="if True, then persons planned for this are on leave",
                        default=False,
                    ),
                ),
            ],
            options={
                "verbose_name": "Ward",
                "verbose_name_plural": "Wards",
            },
        ),
    ]
