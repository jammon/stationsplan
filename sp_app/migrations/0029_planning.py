# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('sp_app', '0028_auto_20160125_0632'),
    ]

    operations = [
        migrations.CreateModel(
            name='Planning',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start', models.DateField()),
                ('end', models.DateField(default=datetime.date(2099, 12, 31))),
                ('json', models.CharField(max_length=255)),
                ('version', models.IntegerField(default=0)),
                ('company', models.ForeignKey(to='sp_app.Company')),
                ('person', models.ForeignKey(to='sp_app.Person')),
                ('ward', models.ForeignKey(to='sp_app.Ward')),
            ],
        ),
    ]
