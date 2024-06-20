from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class Game(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

class Question(models.Model):
    text = models.CharField(max_length=255)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

class Guess(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    guesser = models.ForeignKey(User, on_delete=models.CASCADE, related_name='guesses')
    guessed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='guessed')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    correct = models.BooleanField(default=False)