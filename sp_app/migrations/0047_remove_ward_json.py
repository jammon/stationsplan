# Generated by Django 2.2.3 on 2019-07-31 06:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("sp_app", "0046_auto_20190728_0813"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="ward",
            name="json",
        ),
    ]
