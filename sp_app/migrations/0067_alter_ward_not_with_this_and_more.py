# Generated by Django 4.1 on 2022-09-10 04:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sp_app", "0066_ward_on_different_days"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ward",
            name="not_with_this",
            field=models.ManyToManyField(
                blank=True,
                help_text="Diese Funktionen können für eine Person nicht am gleichen Tag geplant werden",
                related_name="shadowing",
                to="sp_app.ward",
                verbose_name="nicht zusammen mit",
            ),
        ),
        migrations.AlterField(
            model_name="ward",
            name="on_different_days",
            field=models.BooleanField(
                default=False,
                help_text="Diese Funktion kann bedarfweise auch an anderen Tagen geplant werden",
                verbose_name="Anders geplante Tage",
            ),
        ),
    ]