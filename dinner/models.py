from django.db import models

class Game(models.Model):
    GETQUESTION = 'get_question'
    LOBBY = 'lobby'
    ACTIVE = 'active'
    FINISHED = 'finished'
    ABANDONED = 'abandoned'
    
    STATUS_CHOICES = [
        (GETQUESTION, 'Get_question'),
        (LOBBY, 'Lobby'),
        (ACTIVE, 'Active'),
        (FINISHED, 'Finished'),
        (ABANDONED, 'Abandoned'),
    ]
    
    host = models.ForeignKey('Player', on_delete=models.CASCADE, related_name='hosted_games', null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=LOBBY)

    def __str__(self):
        return f"Game {self.id} created by {self.host}"


class Player(models.Model):
    name = models.CharField(max_length=30, unique=True)
    guessing = models.BooleanField(default=False)
    guessed_out = models.BooleanField(default=False)
    has_viewed_result = models.BooleanField(default=False)
    bot = models.BooleanField(default=False)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='players', null=True, blank=True)

    def __str__(self):
        return self.name

class Question(models.Model):
    game = models.OneToOneField(Game, on_delete=models.CASCADE)
    question_text = models.CharField(max_length=255)

    def __str__(self):
        return self.question_text

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    answer_text = models.CharField(max_length=100, null=True)

    class Meta:
        unique_together = ('question', 'player')

    def __str__(self):
        return self.answer_text

class Guess(models.Model):

    class Meta:
        verbose_name = "Guess"

    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    guesser = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='guesses')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='guessed')
    correct = models.BooleanField(default=False)

    def __str__(self):
        return f"Guess by {self.guesser.name} for {self.answer_text} guessed {self.guessed_player.name}"