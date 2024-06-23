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
        labels = {
            'question_text':''
        }

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['answer_text']
        labels = {
            'answer_text': 'Your answer',
        }

class GuessForm(forms.ModelForm):

    guessed_player = forms.ModelChoiceField(queryset=None, label='Select player')
    answer_text = forms.ModelChoiceField(queryset=None, label='Select answer')

    class Meta:
        model = Guess
        fields = ['guessed_player', 'answer_text']

    def __init__(self, *args, **kwargs):
        answers = kwargs.pop('chooseable_answers', None)
        players = kwargs.pop('chooseable_players', None)
        
        super(GuessForm, self).__init__(*args, **kwargs)
        
        if answers is not None:
            self.fields['answer_text'].queryset = answers
        else:
            self.fields['answer_text'].queryset = Answer.objects.none()
        
        if players is not None:
            self.fields['guessed_player'].queryset = players
        else:
            self.fields['guessed_player'].queryset = Player.objects.none()