# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sp_app', '0012_remove_changelogging_department'),
    ]

    operations = [
        migrations.RenameField(
            model_name='ward',
            old_name='department',
            new_name='departments',
        ),
    ]
