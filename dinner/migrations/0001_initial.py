# Generated by Django 3.2.25 on 2024-06-21 07:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer_text', models.CharField(max_length=100, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_text', models.CharField(max_length=255)),
                ('game', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='dinner.game')),
            ],
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30, unique=True)),
                ('guessed_out', models.BooleanField(default=False)),
                ('game', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='player', to='dinner.game')),
            ],
        ),
        migrations.CreateModel(
            name='Guess',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('correct', models.BooleanField(default=False)),
                ('answer_text', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dinner.answer')),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dinner.game')),
                ('guessed_player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='guessed', to='dinner.player')),
                ('guesser', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='guesses', to='dinner.player')),
            ],
            options={
                'verbose_name': 'Guess',
            },
        ),
        migrations.AddField(
            model_name='game',
            name='creator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='created_games', to='dinner.player'),
        ),
        migrations.AddField(
            model_name='answer',
            name='player',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dinner.player'),
        ),
        migrations.AddField(
            model_name='answer',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dinner.question'),
        ),
        migrations.AlterUniqueTogether(
            name='answer',
            unique_together={('question', 'player')},
        ),
    ]
