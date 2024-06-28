# Generated by Django 3.2.25 on 2024-06-28 17:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinner', '0014_auto_20240628_1811'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='status',
            field=models.CharField(choices=[('get_question', 'Get_question'), ('lobby', 'Lobby'), ('guessing', 'Guessing'), ('viewing_result', 'Viewing_result'), ('finished', 'Finished')], default='lobby', max_length=15),
        ),
    ]