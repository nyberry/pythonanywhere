from django import forms
from .models import Player, Game, Question, Answer, Guess


class PlayerRegistrationForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ['name']

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_text']

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['answer_text']

class GuessForm(forms.ModelForm):
    class Meta:
        model = Guess
        fields = ['answer_text', 'guessed_player']

    def __init__(self, *args, **kwargs):
        answers = kwargs.pop('answers', None)
        players = kwargs.pop('players', None)
        
        super(GuessForm, self).__init__(*args, **kwargs)
        
        if answers:
            self.fields['answer_text'].queryset = answers
        
        if players:
            self.fields['guessed_player'].queryset = players