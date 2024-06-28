from django.shortcuts import redirect, render, get_object_or_404
from django.apps import apps

from functools import wraps

from .forms import PlayerRegistrationForm
from .models import Player, Answer, Game, Question

from django.http import HttpResponseRedirect
import random
from random import shuffle

def custom_404(request, exception):
    return HttpResponseRedirect('join')


def registration_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        # Check if the player name is in session. Redirect to registration page if not registered

        if 'player_name' not in request.session:
            return redirect('log_in')  
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def log_in(request):

    # Require a player to register with their name before redirecting them to game's join page

    if request.method == 'POST':
        form = PlayerRegistrationForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            if Player.objects.filter(name=name).exists():
                form.add_error(None, f'There is already a guest named {name}.')
                return render(request, 'registration/login.html', {'form': form})        
            Player.objects.create(name=name)
            request.session['player_name'] = name
            return redirect('front_door') 
    else:
        form = PlayerRegistrationForm()

    return render(request, 'registration/login.html', {'form': form})

@registration_required    
def log_out(request):

    # fetch the current player object
    players = Player.objects.all()
    current_player = players.get(name=request.session['player_name'])

    # delete the player_name key from session data  (logs the player out)
    if 'player_name' in request.session:
        del request.session['player_name']

    # Delete the player object
    current_player.delete()

    # If there are no players left, delete all the model objects
    if not Player.objects.count():
        models = apps.get_models() 
        for model in models:
            model.objects.all().delete()

    # Redirect to landing page
    return redirect('join_game')


def reset_game(request):
    app_models = apps.get_models()
    for model in app_models:
        model.objects.all().delete()
    # redirect to landing page
    return redirect('join_game')


# Function to shuffle answer objects
def shuffle_answers():
    # Fetch all answer objects from the database
    answers = list(Answer.objects.all())

    # Shuffle the list of answers
    shuffle(answers)

    # Update each answer object to reflect the new order
    for index, answer in enumerate(answers, start=1):
        answer.display_order = index  
        answer.save()

# Function to create bot player objects
def create_bots(min_players,pk):

    bot_names = ['Bill', 'Ronald', 'Hermione', 'Elon', 'Elvis', 'Warren', 'Marie', 'Goldilocks', 'Adam', 'Ben', 'Carla', 'Denise', 'Eddie', 'Fiona', 'Graham', 'Hamish', 'Icarus', 'James', 'Kevin', 'Laura', 'Marigold' ]
    bot_answers = ['Cheese', 'Custard', 'Fish', 'Wallpaper', 'Ironing', 'Washing machine', "Swimming", 'Fifteen', 'Spain','Belgium', 'Copper', 'Precisely']

    game = Game.objects.get(pk=pk)
    players = Player.objects.filter(game=game)

    question = Question.objects.filter(game=game).first()

    if len(players) < min_players:
        bots_to_create = min_players - len(players)
        for _ in range(bots_to_create):

            # Create the bot player and associate with the current game 
            players = Player.objects.filter(game=game)
            player_names = [player.name for player in players]
            available_bot_names = [name for name in bot_names if name not in player_names]
            bot_name = random.choice(available_bot_names)
            bot = Player.objects.create(name=bot_name, game=game, bot=True)
            
            # Create the bot's answer and associate with the bot and the current game
            answers = Answer.objects.filter(question = question)
            answers_given = [answer.answer_text for answer in answers]
            available_bot_answers = [answer for answer in bot_answers if answer not in answers_given]
            bot_answer = random.choice(available_bot_answers)
            Answer.objects.create(question=question, player=bot, answer_text=bot_answer, display_order = 0)

            print (f'Created a bot {bot.name} who answered {bot_answer}')

            