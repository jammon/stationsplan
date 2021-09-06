# Generated by Django 2.2.10 on 2020-12-12 14:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sp_app", "0049_calculatedholiday"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="company",
            name="extra_holidays",
        ),
        migrations.RemoveField(
            model_name="region",
            name="holidays",
        ),
        migrations.AddField(
            model_name="region",
            name="calc_holidays",
            field=models.ManyToManyField(
                related_name="regions",
                to="sp_app.CalculatedHoliday",
                verbose_name="Feiertage",
            ),
        ),
    ]
