from django.shortcuts import redirect, render, get_object_or_404
from django.apps import apps

from functools import wraps

from .forms import PlayerRegistrationForm
from .models import Player, Game

from django.http import HttpResponseRedirect

def custom_404(request, exception):
    return HttpResponseRedirect('join')


def registration_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        # Check if the player name is in session. Redirect to registration page if not registered

        if 'player_name' not in request.session:
            return redirect('register_player')  
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def register_player(request):

    # Require a player to register with their name before redirecting them to game's join page

    if request.method == 'POST':
        form = PlayerRegistrationForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            if Player.objects.filter(name=name).exists():
                form.add_error(None, f'There is already a guest named {name}.')
                return render(request, 'registration/welcome.html', {'form': form})        
            Player.objects.create(name=name)
            request.session['player_name'] = name
            return redirect('join_game') 
    else:
        form = PlayerRegistrationForm()

    return render(request, 'registration/welcome.html', {'form': form})

@registration_required    
def log_out(request):

    # fetch the current player and game objects
    players = Player.objects.all()
    current_player = players.get(name=request.session['player_name'])
    current_game =  get_object_or_404(Game, pk = current_player.game.id)

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