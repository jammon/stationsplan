# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sp_app', '0020_auto_20151221_0623'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='changelogging',
            options={'ordering': ['day']},
        ),
        migrations.AlterModelOptions(
            name='changingstaff',
            options={},
        ),
        migrations.RemoveField(
            model_name='changelogging',
            name='person_name',
        ),
        migrations.RemoveField(
            model_name='changelogging',
            name='user_name',
        ),
        migrations.RemoveField(
            model_name='changelogging',
            name='ward_continued',
        ),
        migrations.RemoveField(
            model_name='changelogging',
            name='ward_name',
        ),
        migrations.AddField(
            model_name='changelogging',
            name='description',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='changelogging',
            name='json',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
    ]
