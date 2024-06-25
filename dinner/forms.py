from django import forms
from .models import Player, Game, Question, Answer, Guess


class PlayerRegistrationForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ['name']
        labels = {
            'name':''
        }
        widgets = {
            'name': forms.TextInput(attrs={'id': 'focus-text-field', 'class': 'form-control'})
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_text']
        labels = {
            'question_text':''
        }
        widgets = {
            'question_text': forms.TextInput(attrs={'id': 'focus-text-field', 'class': 'form-control'})
        }

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['answer_text']
        labels = {
            'answer_text': '',
        }
        widgets = {
            'answer_text': forms.TextInput(attrs={'id': 'focus-text-field', 'class': 'form-control'})
        }
