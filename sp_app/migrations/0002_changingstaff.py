# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("sp_app", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChangingStaff",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        primary_key=True,
                        verbose_name="ID",
                        auto_created=True,
                    ),
                ),
                ("day", models.DateField()),
                ("added", models.BooleanField()),
                (
                    "person",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="sp_app.Person"
                    ),
                ),
                (
                    "ward",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="sp_app.Ward"
                    ),
                ),
            ],
        ),
    ]
