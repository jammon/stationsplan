# Generated by Django 4.0.3 on 2022-05-14 16:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sp_app', '0055_auto_20220127_0929'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='employee',
            options={'permissions': [('is_company_admin', 'is admin of the company'), ('is_dep_lead', 'is leader of a department'), ('is_editor', 'is editor for a department')], 'verbose_name': 'Bearbeiter', 'verbose_name_plural': 'Bearbeiter'},
        ),
        migrations.AlterModelOptions(
            name='ward',
            options={'ordering': ['position', 'name'], 'verbose_name': 'Funktion', 'verbose_name_plural': 'Funktionen'},
        ),
        migrations.AddField(
            model_name='person',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, verbose_name='E-Mail-Adresse'),
        ),
        migrations.AddField(
            model_name='ward',
            name='in_ical_feed',
            field=models.BooleanField(default=False, help_text='This function should be part of the ical feed', verbose_name='Part of ical feed'),
        ),
        migrations.AlterField(
            model_name='calculatedholiday',
            name='day',
            field=models.IntegerField(help_text='Tag des Monats oder Anzahl der Tage vor/nach Ostern', verbose_name='Tag'),
        ),
        migrations.AlterField(
            model_name='ward',
            name='after_this',
            field=models.ManyToManyField(blank=True, help_text='Wenn etwas ausgewählt ist, kann der Diensthabende am nächsten Tag nur für diese Funktionen verplant werden', related_name='predecessor', to='sp_app.ward', verbose_name='Folgeschicht'),
        ),
        migrations.AlterField(
            model_name='ward',
            name='callshift',
            field=models.BooleanField(default=False, help_text='Diese Funktion soll als Bereitschaftsdienst dargestellt werden.', verbose_name='Bereitschaftsdienst'),
        ),
        migrations.AlterField(
            model_name='ward',
            name='not_with_this',
            field=models.ManyToManyField(blank=True, help_text='Diese Funktionen können für eine Person nicht am gleichen Tag plant werden', related_name='shadowing', to='sp_app.ward', verbose_name='nicht zusammen mit'),
        ),
        migrations.CreateModel(
            name='FeedId',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uid', models.CharField(max_length=20, verbose_name='ID')),
                ('active', models.BooleanField(default=True)),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feed_ids', to='sp_app.person')),
            ],
            options={
                'verbose_name': 'FeedId',
                'verbose_name_plural': 'FeedIds',
            },
        ),
    ]