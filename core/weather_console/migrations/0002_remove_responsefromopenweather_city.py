# Generated by Django 5.1.4 on 2024-12-10 13:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('weather_console', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='responsefromopenweather',
            name='city',
        ),
    ]
