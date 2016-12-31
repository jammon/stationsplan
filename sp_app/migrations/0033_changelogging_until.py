# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sp_app', '0032_auto_20161127_0631'),
    ]

    operations = [
        migrations.AddField(
            model_name='changelogging',
            name='until',
            field=models.DateField(help_text='Date when the change ends. Can be blank.', null=True, blank=True),
        ),
    ]
