# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("sp_app", "0017_auto_20151115_1532"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="company",
            options={
                "verbose_name": "Krankenhaus",
                "verbose_name_plural": "Krankenh\xe4user",
            },
        ),
        migrations.AlterModelOptions(
            name="department",
            options={
                "verbose_name": "Abteilung",
                "verbose_name_plural": "Abteilungen",
            },
        ),
        migrations.AlterModelOptions(
            name="person",
            options={
                "verbose_name": "Person",
                "verbose_name_plural": "Personen",
            },
        ),
        migrations.AlterModelOptions(
            name="ward",
            options={
                "verbose_name": "Funktion",
                "verbose_name_plural": "Funktionen",
            },
        ),
        migrations.AlterField(
            model_name="company",
            name="shortname",
            field=models.CharField(max_length=10, verbose_name="Kurzname"),
        ),
        migrations.AlterField(
            model_name="department",
            name="company",
            field=models.ForeignKey(
                related_name="departments",
                on_delete=django.db.models.deletion.CASCADE,
                to="sp_app.Company",
                help_text="Die oberste Organisationseinheit",
            ),
        ),
        migrations.AlterField(
            model_name="department",
            name="shortname",
            field=models.CharField(max_length=10, verbose_name="Kurzname"),
        ),
        migrations.AlterField(
            model_name="person",
            name="departments",
            field=models.ManyToManyField(
                related_name="persons",
                verbose_name="Abteilungen",
                to="sp_app.Department",
            ),
        ),
        migrations.AlterField(
            model_name="person",
            name="end_date",
            field=models.DateField(
                default=datetime.date(2099, 12, 31),
                help_text="Dienstende",
                verbose_name="Endedatum",
            ),
        ),
        migrations.AlterField(
            model_name="person",
            name="functions",
            field=models.ManyToManyField(
                help_text="Funktionen, die er oder sie aus\xfcben kann",
                related_name="staff",
                verbose_name="Wards",
                to="sp_app.Ward",
            ),
        ),
        migrations.AlterField(
            model_name="person",
            name="position",
            field=models.IntegerField(
                default=1,
                help_text="Position in der Anzeige",
                verbose_name="Position",
            ),
        ),
        migrations.AlterField(
            model_name="person",
            name="shortname",
            field=models.CharField(max_length=10, verbose_name="Kurzname"),
        ),
        migrations.AlterField(
            model_name="person",
            name="start_date",
            field=models.DateField(
                default=datetime.date(2015, 1, 1),
                help_text="Dienstantritt",
                verbose_name="Anfangsdatum",
            ),
        ),
        migrations.AlterField(
            model_name="ward",
            name="approved",
            field=models.DateField(
                help_text="Das Datum, bis zu dem der Plan genehmigt ist",
                null=True,
                blank=True,
            ),
        ),
        migrations.AlterField(
            model_name="ward",
            name="continued",
            field=models.BooleanField(
                default=True,
                help_text="wenn Wahr, dann wird die heutige Besetzung i.d.R. auch f\xfcr morgen geplant",
                verbose_name="fortsetzen",
            ),
        ),
        migrations.AlterField(
            model_name="ward",
            name="departments",
            field=models.ManyToManyField(
                related_name="wards",
                verbose_name="Abteilungen",
                to="sp_app.Department",
            ),
        ),
        migrations.AlterField(
            model_name="ward",
            name="everyday",
            field=models.BooleanField(
                default=False,
                help_text="wenn Wahr, dann muss diese Funktion auch an freien Tagen geplant werden",
                verbose_name="t\xe4glich",
            ),
        ),
        migrations.AlterField(
            model_name="ward",
            name="freedays",
            field=models.BooleanField(
                default=False,
                help_text="wenn Wahr, dann kann diese Funktion nur an freien Tagen geplant werden",
                verbose_name="freie Tage",
            ),
        ),
        migrations.AlterField(
            model_name="ward",
            name="max",
            field=models.IntegerField(help_text="Maximale Besetzung"),
        ),
        migrations.AlterField(
            model_name="ward",
            name="min",
            field=models.IntegerField(help_text="Minimale Besetzung"),
        ),
        migrations.AlterField(
            model_name="ward",
            name="nightshift",
            field=models.BooleanField(
                default=False,
                help_text="wenn Wahr, dann kann der Diensthabende nicht f\xfcr den n\xe4chsten Tag verplant werden",
                verbose_name="Nachtdienst",
            ),
        ),
        migrations.AlterField(
            model_name="ward",
            name="on_leave",
            field=models.BooleanField(
                default=False,
                help_text="wenn Wahr, dann stehen die hier eingetragenen Personen nicht zur Arbeit zur Verf\xfcgung",
                verbose_name="Urlaub/frei",
            ),
        ),
        migrations.AlterField(
            model_name="ward",
            name="position",
            field=models.IntegerField(
                default=1, help_text="Position in der Anzeige"
            ),
        ),
        migrations.AlterField(
            model_name="ward",
            name="shortname",
            field=models.CharField(max_length=10, verbose_name="Kurzname"),
        ),
    ]
