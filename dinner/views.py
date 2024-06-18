from django.shortcuts import render
from django.http import HttpResponse

game_started=False

def welcome(request):
    global game_started
    action = request.GET.get('action')
    if action == 'start':
        # Handle the logic for starting a new game
        game_started= True
        return HttpResponse("Starting a new game...")
    elif action == "join":
        # Handle the logic for starting a new game
        return HttpResponse("Joining the game...")
    else:
        # Default behavior for the index route
        return render(request, 'dinner/welcome.html', {"game_started":game_started})