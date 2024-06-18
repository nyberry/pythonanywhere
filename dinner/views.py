from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
import markdown2
import os

game_started=False

def apology(request, message, code=400):
    return render (request, 'apology.html', {"top":code, "bottom":message})

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def gethostname(request):
    global game_started
    if request.method == "POST":
        action = request.POST.get('action')
        if action == 'next':
            # handle host username provided
            username = request.POST.get("username")
            username, error = validate_username(username)
            if error:
                return apology(request, f'{error}', 400)
            else:
                user_ip = get_client_ip(request)
                print(f"User IP address: {user_ip}")
                return HttpResponse(f'Hello {username} your IP address is {user_ip}')
        elif action == 'home':
            # Handle 'home' action
            game_started = False
            return redirect(reverse('welcome'))

    else:
        # display the form to get the user request
        return render (request, 'dinner/gethostname.html')
    
def validate_username(username):
    # check a username was provided
    if not username:
        return None, "please provide name"
    if len(username) > 20:
        username = username[:20]
    # Ensure username does not already exist:
    # username_existing_entry = db.execute("SELECT * FROM users WHERE username = ?", username)
    # if len(username_existing_entry) != 0:
    #    print(username_existing_entry)
    #    return None, "username already in use"
    # Username is valid
    return username, None

def welcome(request):
    global game_started
    print (f'Game started = {game_started}')
    action = request.GET.get('action')
    if action == 'start' and game_started == False:
        # Handle the logic for starting a new game
        game_started= True
        return redirect(reverse('gethostname'))
    elif action == "join" or (action =="start" and game_started != False):
        # Handle the logic for joining an existing game
        return HttpResponse("Joining the game...")
    elif action == "about":
        # Show info about the game
        return render(request, 'dinner/about.html')
    elif action == "development":
        # Show info about the game's development
        current_dir = os.path.dirname(__file__)
        readme_path = os.path.join(current_dir, '..', 'README.md')
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_content = f.read()
        html_content = markdown2.markdown(readme_content)
        return render(request, 'dinner/development.html', {'html_content': html_content})
    else:
        # Default behavior for the index route
        return render(request, 'dinner/welcome.html', {"game_started":game_started})
    
    