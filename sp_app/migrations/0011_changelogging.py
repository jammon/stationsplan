# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sp_app', '0010_auto_20151024_0807'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChangeLogging',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('day', models.DateField()),
                ('added', models.BooleanField()),
                ('user_name', models.CharField(max_length=20)),
                ('person_name', models.CharField(max_length=20)),
                ('ward_name', models.CharField(max_length=20)),
                ('ward_continued', models.BooleanField()),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sp_app.Company')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sp_app.Department')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sp_app.Person')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('ward', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sp_app.Ward')),
            ],
        ),
    ]
