# Generated by Django 2.0 on 2018-05-02 18:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sp_app', '0041_auto_20180501_0713'),
    ]

    operations = [
        migrations.CreateModel(
            name='DifferentDay',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.DateField(help_text='Day that is different', verbose_name='day')),
                ('added', models.BooleanField(help_text='Planning is additional (not cancelled)', verbose_name='additional')),
                ('ward', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='different_days', to='sp_app.Ward')),
            ],
        ),
    ]