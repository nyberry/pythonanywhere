# Generated by Django 3.2.25 on 2024-06-28 15:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinner', '0013_auto_20240628_1339'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='game',
            name='round',
        ),
        migrations.AddField(
            model_name='player',
            name='has_acknowledged_winner',
            field=models.BooleanField(default=True),
        ),
    ]
