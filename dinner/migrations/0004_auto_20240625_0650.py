# Generated by Django 3.2.25 on 2024-06-25 03:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinner', '0003_game_status'),
    ]

    operations = [
        migrations.RenameField(
            model_name='guess',
            old_name='answer_text',
            new_name='guessed_answer',
        ),
        migrations.AlterField(
            model_name='game',
            name='status',
            field=models.CharField(choices=[('get_question', 'Get_question'), ('lobby', 'Lobby'), ('active', 'Active'), ('finished', 'Finished'), ('abandoned', 'Abandoned')], default='lobby', max_length=15),
        ),
    ]
