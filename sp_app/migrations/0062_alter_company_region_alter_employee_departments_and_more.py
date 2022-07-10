# Generated by Django 4.0.5 on 2022-06-29 04:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sp_app', '0061_alter_region_options_statusentry_timestamp'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='region',
            field=models.ForeignKey(blank=True, help_text='Bundesland, dessen Feiertage für dieses Krankenhaus gelten.', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='companies', to='sp_app.region'),
        ),
        migrations.AlterField(
            model_name='employee',
            name='departments',
            field=models.ManyToManyField(related_name='employees', to='sp_app.department', verbose_name='Abteilung'),
        ),
        migrations.AlterField(
            model_name='ward',
            name='after_this',
            field=models.ManyToManyField(blank=True, help_text='Wenn etwas ausgewählt ist, kann die Diensthabende am nächsten Tag nur für diese Funktionen verplant werden', related_name='predecessor', to='sp_app.ward', verbose_name='Folgeschicht'),
        ),
        migrations.AlterField(
            model_name='ward',
            name='in_ical_feed',
            field=models.BooleanField(default=False, help_text='Diese Funktion soll im Kalender-Feed angezeigt werden', verbose_name='Im Kalender-Feed'),
        ),
        migrations.AlterUniqueTogether(
            name='person',
            unique_together={('name', 'company'), ('shortname', 'company')},
        ),
    ]