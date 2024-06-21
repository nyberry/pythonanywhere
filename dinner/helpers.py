from functools import wraps
from django.shortcuts import redirect


def registration_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if the player name is in session
        if 'player_name' not in request.session:
            return redirect('register_player')  # Redirect to registration page if not registered
        
        return view_func(request, *args, **kwargs)
    
    return wrapper