# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sp_app', '0034_auto_20170102_2245'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='wardtype',
            options={'verbose_name': 'Funktionsart', 'verbose_name_plural': 'Funktionsarten'},
        ),
        migrations.AlterField(
            model_name='person',
            name='functions',
            field=models.ManyToManyField(help_text='Funktionen, die er oder sie aus\xfcben kann', related_name='staff', verbose_name='Funktionen', to='sp_app.Ward'),
        ),
        migrations.AlterField(
            model_name='planning',
            name='superseded_by',
            field=models.ForeignKey(related_name='supersedes', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='sp_app.Planning', help_text='Sp\xe4tere Planung, die diese hier \xfcberdeckt', null=True),
        ),
        migrations.AlterField(
            model_name='ward',
            name='after_this',
            field=models.ManyToManyField(help_text='wenn etwas ausgew\xe4hlt ist, kann der Diensthabende am n\xe4chsten Tag nur f\xfcr diese Funktionen verplant werden', to='sp_app.Ward', blank=True),
        ),
    ]
