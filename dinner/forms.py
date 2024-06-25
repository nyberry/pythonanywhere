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
            'question_text': ''
        }
        widgets = {
            'question_text': forms.TextInput(attrs={'id': 'focus-text-field', 'class': 'form-control'})
        }

    def clean_question_text(self):
        question_text = self.cleaned_data.get('question_text')
        if question_text:
            # Capitalize the first letter
            question_text = question_text[0].upper() + question_text[1:]

            # Add a question mark at the end if there isn't one already
            if not question_text.endswith('?'):
                question_text = question_text + '?'
        
        return question_text


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
