# Generated by Django 3.2.25 on 2024-06-25 03:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dinner', '0004_auto_20240625_0650'),
    ]

    operations = [
        migrations.RenameField(
            model_name='guess',
            old_name='guessed_answer',
            new_name='answer',
        ),
        migrations.RenameField(
            model_name='guess',
            old_name='guessed_player',
            new_name='player',
        ),
    ]