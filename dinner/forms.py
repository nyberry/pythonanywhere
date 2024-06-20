from django import forms
from .models import Answer, Guess, Question

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text']

class GuessForm(forms.ModelForm):
    class Meta:
        model = Guess
        fields = ['answer', 'guessed_user']

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'game']