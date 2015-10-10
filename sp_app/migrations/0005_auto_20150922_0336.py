# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sp_app', '0004_auto_20150912_2250'),
    ]

    operations = [
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(verbose_name='Name', max_length=50)),
                ('company', models.CharField(verbose_name='Company', help_text='The top organizational unit', max_length=50)),
            ],
            options={
                'verbose_name': 'Department',
                'verbose_name_plural': 'Departments',
            },
        ),
        migrations.AlterModelOptions(
            name='changingstaff',
            options={'ordering': ['day']},
        ),
        migrations.AddField(
            model_name='person',
            name='department',
            field=models.ForeignKey(null=True, to='sp_app.Department'),
        ),
        migrations.AddField(
            model_name='ward',
            name='department',
            field=models.ManyToManyField(to='sp_app.Department'),
        ),
    ]
