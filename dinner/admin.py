from django.contrib import admin
from .models import Game, Player, Question, Answer, Guess

admin.site.register(Game)
admin.site.register(Player)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Guess)