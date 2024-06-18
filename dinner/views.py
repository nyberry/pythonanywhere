from django.shortcuts import render
from django.http import HttpResponse
import markdown2
import os

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
    elif action == "about":
        return render(request, 'dinner/about.html')
    elif action == "development":
        current_dir = os.path.dirname(__file__)
        readme_path = os.path.join(current_dir, '..', 'README.md')
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_content = f.read()
        html_content = markdown2.markdown(readme_content)
        return render(request, 'dinner/development.html', {'html_content': html_content})
    else:
        # Default behavior for the index route
        return render(request, 'dinner/welcome.html', {"game_started":game_started})
    
    