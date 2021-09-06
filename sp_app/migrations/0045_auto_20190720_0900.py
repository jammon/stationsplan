# Generated by Django 2.2.3 on 2019-07-20 07:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sp_app", "0044_auto_20180810_1503"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="differentday",
            options={
                "verbose_name": "Anders geplanter Tag",
                "verbose_name_plural": "Anders geplante Tage",
            },
        ),
        migrations.AlterField(
            model_name="differentday",
            name="added",
            field=models.BooleanField(
                help_text="Die Funktion wird an diesem Tag zusätzlich geplant (nicht gestrichen).",
                verbose_name="zusätzlich",
            ),
        ),
        migrations.AlterField(
            model_name="differentday",
            name="day",
            field=models.DateField(
                help_text="Tag, der anders geplant wird.", verbose_name="Tag"
            ),
        ),
        migrations.AlterField(
            model_name="person",
            name="position",
            field=models.IntegerField(
                default=1,
                help_text="Position in der Anzeige. Sollte nicht mehr als zwei Stellen haben.",
                verbose_name="Position",
            ),
        ),
        migrations.AlterField(
            model_name="ward",
            name="callshift",
            field=models.BooleanField(
                default=False,
                help_text="Diese Funktion soll als Bereitschaftsdienst behandelt werden.",
                verbose_name="Bereitschaftsdienst",
            ),
        ),
        migrations.AlterField(
            model_name="ward",
            name="freedays",
            field=models.BooleanField(
                default=False,
                help_text="Diese Funktion kann nur an freien Tagen geplant werden.",
                verbose_name="freie Tage",
            ),
        ),
        migrations.AlterField(
            model_name="ward",
            name="position",
            field=models.IntegerField(
                default=1,
                help_text="Position in der Anzeige. Sollte nicht mehr als zwei Stellen haben.",
            ),
        ),
        migrations.AlterField(
            model_name="ward",
            name="weekdays",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Wochentage, an denen diese Funktion geplant werden soll. (Reihe von Ziffern, 0 für Sonntag.)",
                max_length=7,
                verbose_name="Wochentage",
            ),
        ),
    ]
