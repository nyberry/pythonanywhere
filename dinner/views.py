from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.urls import reverse
from django.db.models import Max
from .models import Player, Game, Question, Answer, Guess
from .forms import QuestionForm, AnswerForm, GuessForm, PlayerRegistrationForm
from .helpers import registration_required
from django.db import IntegrityError

def register_player(request):

    # Require a player to register with their name before redirecting them to game's join page

    if request.method == 'POST':
        form = PlayerRegistrationForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            if Player.objects.filter(name=name).exists():
                return render(request, 'registration/welcome.html', {'form': form})        
            Player.objects.create(name=name)
            request.session['player_name'] = name
            return redirect('join_game') 
    else:
        form = PlayerRegistrationForm()
        return render(request, 'registration/welcome.html', {'form': form})

@registration_required
def join_game(request):

    # This is the landing page. If there are no games, create a game now.
    games = Game.objects.all()
    if not games:
        return redirect('start_new_game')

    # Load the most recently created game
    most_recent_game_id = games.aggregate(Max('id'))['id__max']
    game = get_object_or_404(Game, pk=most_recent_game_id)

    # if the last game has lobby status, direct the player to the question page of that game
    if game.status == "lobby":
        return redirect(reverse('ask_question', kwargs={'pk': most_recent_game_id}))

    # Else if the last game has active status, direct the player to the spectator page for that game
    elif game.status == "active":
        return HttpResponse("Wait for the next game to be started...")

    # Else if the last game has status finished, create a new game
    else:
        return redirect('start_new_game')


@registration_required
def ask_question(request, pk):

    # This is the lobby page where players are asked a question, and then wait until the game starts.
    game = get_object_or_404(Game, pk=pk)

    # If there is no question yet, go to a holding page
    if not game.question:
        return render(request,'dinner/wait_for_question.html',{'host':game.creator})

    # Fetch the current player object from session data, and update their game and guessed status fields
    players = Player.objects.all()
    current_player = Player.objects.get(name=request.session['player_name'])
    current_player.game = game
    current_player.guessed_out= False
    current_player.save()
    
    # Fetch the current game question and the answers given so far
    question = game.question 
    answers = Answer.objects.filter(question=question)

    # Check if the current player has already answered this question. If so, redirect to guess page
    has_answered = Answer.objects.filter(question=question, player=current_player).exists()
    if has_answered:
        return redirect(reverse('guess', kwargs={'pk': pk}))

    # Otherwise, render the page to ask the question using POST method
    
    if request.method == "POST":
        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(commit=False)
            answer.question = question
            answer.player = current_player 
            try:
                answer.save()
            except IntegrityError:
                form.add_error(None, "You have already answered this question.")
            return redirect('ask_question', pk=game.pk)
    else:
        form = AnswerForm()
    return render(request, 'dinner/ask_question.html', {'game': game, 'question': question, 'answers': answers, 'form': form, 'players':players})


@registration_required
def guess(request, pk):
   
    # fetch the game, question and player objects
    game = get_object_or_404(Game, pk=pk) 
    players = Player.objects.filter(game=game)
    current_player = players.get(name=request.session['player_name'])

    # redirect to loser page if current player is guessed out
    if current_player.guessed_out==True:
         return redirect('loser_page',pk=pk)
    
    # Fetch players who are not guessed out
    remaining_players = players.filter(guessed_out=False)
    
    # Fetch answers for the current game where the player is not guessed out
    answers = Answer.objects.filter(question__game=game)
    remaining_answers = answers.filter(player__guessed_out=False)
    
    # Exclude the current player and their answer from the list of chooseable players and answers
    chooseable_players = remaining_players.exclude(id=current_player.id)
    chooseable_answers = remaining_answers.exclude(player__id=current_player.id)

    # handle the guess
    if request.method == "POST":
        form = GuessForm(request.POST,chooseable_answers=chooseable_answers, chooseable_players=chooseable_players)
        if form.is_valid():
            guess = form.save(commit=False)
            guess.guesser = current_player
          
            # Check if the guessed answer and guessed player match
            guessed_answer = form.cleaned_data['answer_text']
            guessed_player = form.cleaned_data['guessed_player']
            guess.correct = (guessed_answer.player == guessed_player)
            guess.game = game
            guess.save()

            if guess.correct:
                guessed_player.guessed_out = True
                guessed_player.save()

                # Check if only one player remains in the game
                remaining_players_count = Player.objects.filter(game=game, guessed_out=False).count()
                if remaining_players_count == 1:
                    # Redirect to the winner page if only one player remains
                    game.status='FINISHED'
                    game.save()
                    return redirect('winner_page',pk=pk)

            return render(request, 'dinner/result.html', {'correct': guess.correct, 'game': game, 'guessed_player': guessed_player, 'guessed_answer': guessed_answer})
           
    else:
        form = GuessForm(chooseable_answers=chooseable_answers, chooseable_players=chooseable_players)
    
    return render(request, 'dinner/guess.html', {'form': form, 'game': game, 'question':game.question, 'answers': answers, 'players':players, 'current_player':current_player, 'remaining_answers': remaining_answers, 'remaining_players':remaining_players})


@registration_required
def start_new_game(request):
    current_player = Player.objects.get(name=request.session['player_name'])
    game = Game.objects.create(creator=current_player)
    game.status = 'lobby'
    game.save()

    if request.method == 'POST':
        question_form = QuestionForm(request.POST)
        if question_form.is_valid():          
            question = question_form.save(commit=False)
            question.game = game
            question.save()
            return redirect('ask_question', pk=game.pk)
    else:
        question_form = QuestionForm()
    
    context = {
        'question_form': question_form,
        'current_player': current_player
    }
    return render(request, 'dinner/start_new_game.html', context)

@registration_required
def reset_game(request, pk):
    game = get_object_or_404(Game, pk=pk)  # Retrieve the game object
    game.status = 'abandoned'
    game.save()
    return redirect('join_game', pk=game.pk)

@registration_required
def winner_page(request, pk):
    game = get_object_or_404(Game, pk=pk)  # Retrieve the game object
    players = Player.objects.filter(game=game)  # Fetch all players
    remaining_players = Player.objects.filter(game=game, guessed_out=False)  # Fetch remaining players
    answers = Answer.objects.filter(question__game=game)  # Fetch all answers
    remaining_answers = Answer.objects.filter(question__game=game, player__guessed_out=False)  # Fetch remaining answers
    
    context = {
        'players': players,
        'remaining_players': remaining_players,
        'answers': answers,
        'remaining_answers': remaining_answers,
    }
    
    return render(request, 'dinner/winner_page.html', context)

@registration_required
def loser_page(request, pk):
    game = get_object_or_404(Game, pk=pk)  # Retrieve the game object
    players = Player.objects.filter(game=game)  # Fetch all players
    remaining_players = Player.objects.filter(game=game, guessed_out=False)  # Fetch remaining players
    answers = Answer.objects.filter(question__game=game)  # Fetch all answers
    remaining_answers = Answer.objects.filter(question__game=game, player__guessed_out=False)  # Fetch remaining answers
    
    context = {
        'players': players,
        'remaining_players': remaining_players,
        'answers': answers,
        'remaining_answers': remaining_answers,
    }
    
    return render(request, 'dinner/loser_page.html', context)