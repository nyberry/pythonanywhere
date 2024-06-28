# Generated by Django 3.2.25 on 2024-06-28 10:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinner', '0012_auto_20240628_1208'),
    ]

    operations = [
        migrations.RenameField(
            model_name='player',
            old_name='has_viewed_result',
            new_name='has_acknowledged_result',
        ),
        migrations.AlterField(
            model_name='game',
            name='status',
            field=models.CharField(choices=[('get_question', 'Get_question'), ('lobby', 'Lobby'), ('guessing', 'Guessing'), ('viewing_results', 'Viewing_results'), ('finished', 'Finished')], default='lobby', max_length=15),
        ),
    ]