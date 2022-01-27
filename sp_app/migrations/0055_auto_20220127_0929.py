# Generated by Django 3.2.5 on 2022-01-27 08:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sp_app', '0054_auto_20210526_1039'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Holiday',
        ),
        migrations.AddField(
            model_name='ward',
            name='not_with_this',
            field=models.ManyToManyField(blank=True, help_text='these functions can not be planned on the same day', related_name='shadowing', to='sp_app.Ward', verbose_name='not with this'),
        ),
        migrations.AlterField(
            model_name='ward',
            name='after_this',
            field=models.ManyToManyField(blank=True, help_text='wenn etwas ausgewählt ist, kann der Diensthabende am nächsten Tag nur für diese Funktionen verplant werden', related_name='predecessor', to='sp_app.Ward', verbose_name='Folgeschicht'),
        ),
        migrations.AlterField(
            model_name='ward',
            name='callshift',
            field=models.BooleanField(default=False, help_text='if True, then this function is displayed as call shift', verbose_name='Bereitschaftsdienst'),
        ),
    ]