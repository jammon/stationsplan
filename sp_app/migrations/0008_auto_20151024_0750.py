# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("sp_app", "0007_auto_20150924_0439"),
    ]

    operations = [
        migrations.AddField(
            model_name="employee",
            name="departments",
            field=models.ManyToManyField(
                related_name="employees", to="sp_app.Department"
            ),
        ),
        migrations.AddField(
            model_name="person",
            name="departments",
            field=models.ManyToManyField(
                related_name="persons", to="sp_app.Department"
            ),
        ),
        migrations.AlterField(
            model_name="employee",
            name="department",
            field=models.ForeignKey(
                related_name="employee",
                on_delete=django.db.models.deletion.CASCADE,
                to="sp_app.Department",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="person",
            name="department",
            field=models.ForeignKey(
                related_name="person",
                on_delete=django.db.models.deletion.CASCADE,
                to="sp_app.Department",
                null=True,
            ),
        ),
    ]
