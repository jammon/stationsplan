# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sp_app', '0019_ward_after_this'),
    ]

    operations = [
        migrations.CreateModel(
            name='StatusEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=30)),
                ('content', models.CharField(max_length=255)),
                ('company', models.ForeignKey(related_name='status_entries', blank=True, to='sp_app.Company', help_text='Can be empty', null=True)),
                ('department', models.ForeignKey(related_name='status_entries', blank=True, to='sp_app.Department', help_text='Can be empty', null=True)),
            ],
        ),
        migrations.AlterField(
            model_name='ward',
            name='after_this',
            field=models.ManyToManyField(help_text='if not empty, only these functions can be planned on the next day', to='sp_app.Ward', blank=True),
        ),
    ]
