# Generated by Django 2.1.7 on 2019-03-18 02:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ops', '0005_auto_20181219_1807'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adhoc',
            name='run_as',
            field=models.CharField(default='', max_length=64, null=True, verbose_name='Username'),
        ),
    ]