# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sp_app', '0013_auto_20151027_0537'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='functions',
            field=models.ManyToManyField(help_text='Functions that he or she can  perform', related_name='staff', to='sp_app.Ward'),
        ),
    ]
