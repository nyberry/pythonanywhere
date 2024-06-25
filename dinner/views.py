from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.urls import reverse
from django.db.models import Max
from .models import Player, Game, Question, Answer, Guess
from .forms import QuestionForm, AnswerForm, PlayerRegistrationForm
from .helpers import registration_required
from django.db import IntegrityError
from django.apps import apps
import random
from random import shuffle

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

    # fetch the current player object
    players = Player.objects.all()
    current_player = players.get(name=request.session['player_name'])

    # delete the player_name key from session data  (logs the player out)
    if 'player_name' in request.session:
        del request.session['player_name']

    # Delete the player object
    current_player.delete()
    
    # Redirect to landing page
    return redirect('join_game')


@registration_required
def join_game(request):

    # This is the landing page. If there are no games, create a game now.
    games = Game.objects.all()
    if not games:
        return redirect('start_new_game')

    # Load the most recently created game & store it's id in the session data
    most_recent_game_id = games.aggregate(Max('id'))['id__max']
    game = get_object_or_404(Game, pk=most_recent_game_id)
    request.session['game']=game.pk

    print(f'Game status:{game.status}')

    # if the game has getquestion status, direct the player to the wait_for_question page, or the get_question page if current player is host
    if game.status == "get_question":
        current_player = Player.objects.get(name=request.session['player_name'])
        if current_player != game.host:
            return render(request,'dinner/wait_for_question.html',{'host':game.host, 'current_player':current_player})
        else:
            return redirect('get_question', pk=game.pk)

    # if the game has lobby status, direct the player to the question route for that game
    elif game.status == "lobby":
        return redirect(reverse('ask_question', kwargs={'pk': most_recent_game_id}))

    # Else if the game has active status, direct the player to the spectator route for that game
    elif game.status == "active":
         return redirect(reverse('spectate', kwargs={'pk': most_recent_game_id}))
    
     # if the game has finished status, direct the player to the wait_for_question page
    elif game.status == "finished":
        current_player = Player.objects.get(name=request.session['player_name'])
        winner = Player.objects.filter(game=game, guessed_out=False)[0]
        return render(request,'dinner/wait_for_question.html',{'host':winner.name, 'current_player':current_player})

    # Else if the last game has status abandoned, create a new game
    elif game.status == "abandoned":
        return redirect('start_new_game')


@registration_required
def ask_question(request, pk):

    # This is the lobby page where players are asked a question, and then wait until the game starts.

    # Load the game object and store it's ID (primary key) in the session data
    game = get_object_or_404(Game, pk=pk)

    # redirect to join page if the current game session is 'abandoned'
    if game.status == 'abandoned':
        return redirect('join_game')

    # Fetch the current player object from session data, and update their game and guessed status fields
    current_player = Player.objects.get(name=request.session['player_name'])
    current_player.game = game
    current_player.guessed_out= False
    current_player.save()
    
    # If there is no question yet, go to a holding page
    if not hasattr(game, 'question'):
        return render(request,'dinner/wait_for_question.html',{'host':game.host, 'current_player':current_player})

    # Fetch the current game question and the answers given so far
    question = game.question 
    answers = Answer.objects.filter(question=question)

    # Check if the current player has already answered this question. If so, redirect to guess page
    has_answered = Answer.objects.filter(question=question, player=current_player).exists()
    if has_answered:
        return redirect(reverse('lobby', kwargs={'pk': pk}))

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
        
        context = {
            'form': AnswerForm(),
            'current_player': current_player,
            'question': question
            }
    
    return render(request, 'dinner/ask_question.html', context)

@registration_required
def lobby(request, pk):
    
    # fetch the game objects
    game = get_object_or_404(Game, pk=pk)

    # if the host has pressed the button to start the game
    if request.method == "POST":
        if request.POST.get('start'):
            game.status ="active"
            game.save()

            # Create bot players to make the minimum number for a game
            MIN_PLAYERS = 6
            bot_names = ['Harry', 'Charlie', 'Boticelli', 'Robert', 'Elizabot']
            bot_answers = ['Cheese', 'Custard', 'Fish', 'Wallpaper', 'Ironing', 'Washing machine', "Swimming", 'Fifteen', 'Spain','Rarely']
            players = Player.objects.filter(game=pk)
            game = Game.objects.get(pk=pk)

            if len(players) < MIN_PLAYERS:
                bots_to_create = MIN_PLAYERS - len(players)
                for i in range(bots_to_create):

                    # Create the bot player and associate with the current game            
                    bot = Player.objects.create(name=f'{bot_names[i]}{pk}', game=game, bot = True)
                    
                    # Create the bot's answer and associate with the bot and the current game
                    question = Question.objects.filter(game=game).first()
                    Answer.objects.create(question=question, player=bot, answer_text=random.choice(bot_answers))

            # Select a random player to be the guesser, and set all the others to not be guessers
            players = Player.objects.filter(game=pk)
            players.update(guessing = False)
            human_players = players.filter(bot=False)
            guesser = random.choice(human_players)
            guesser.guessing = True
            guesser.save()

    # redirect to guess page if the current game session is now active
    if game.status == 'active':
        return redirect('guess', pk=pk)

    # redirect to join page if the current game session is not lobby
    elif game.status != 'lobby':
        return redirect('join_game')
    
    # fetch the players who have answered the current question, and render the lobby page
    current_question = get_object_or_404(Question, game=game)
    players = Player.objects.filter(game=game)
    current_player = players.get(name=request.session['player_name'])
    players_with_answers = players.filter(answer__question=current_question).distinct()

    context = {
        'game_id': pk,
        'question': game.question,
        'players': players_with_answers,
        'current_player': current_player,
        'host': game.host
    }
    return render(request, 'dinner/lobby.html', context)


@registration_required
def guess(request, pk):
   
    # fetch the game, question and player objects
    game = get_object_or_404(Game, pk=pk) 
    players = Player.objects.filter(game=game)
    current_player = players.get(name=request.session['player_name'])
    guessing_player = Player.objects.filter(guessing=True).first()

    # redirect to join page if the current game session is not active
    if game.status == 'abandoned':
        return redirect('join_game')

    # redirect to loser page if current player is guessed out
    if current_player.guessed_out==True:
         return redirect('loser_page',pk=pk)
    
    # if all of the remaining human players have status "has viewed result", then we are done with the results page. reset all flags to False
    human_players = players.filter(game=game, bot=False, guessed_out = False)
    if not human_players.filter(has_viewed_result=False).exists():
        players.update(has_viewed_result=False)
    
    for p in human_players:
        print (p.name,"has viewed result:", p.has_viewed_result)

    # redirect to the results route if any player has status 'has viewed result' because this means the guess is in
    if players.filter(has_viewed_result=True).exists():
        return redirect('view_result',pk=pk)
    
    # Fetch players who are not guessed out, and exclude the current player from the list of chooseable players
    remaining_players = players.filter(guessed_out=False)
    chooseable_players = list(remaining_players.exclude(id=current_player.id))
 
    # Fetch and shuffle answers for the current game where the player is not guessed out
    answers = Answer.objects.filter(question__game=game)
    remaining_answers = answers.filter(player__guessed_out=False)
    chooseable_answers = list(remaining_answers.exclude(player__id=current_player.id))
    shuffle(chooseable_answers)

    # handle the guess
    if request.method == "POST":

        guessed_player_id = request.POST.get('player')
        guessed_answer_id = request.POST.get('answer')

        if guessed_answer_id and guessed_player_id:

            # a guess was made

            guessed_player = Player.objects.get(id=guessed_player_id, game=game)
            guessed_answer = Answer.objects.get(id=guessed_answer_id, question__game=game)

            guess = Guess.objects.create(
                answer=guessed_answer,
                player=guessed_player,
                game=game,
                guesser=current_player,
                correct=(guessed_player == guessed_answer.player)
            )

            if guess.correct:
                guess.player.guessed_out = True
                guess.player.save()

            # Recount the humans players. Check if only one player remains in the game & redirect to winner page if so.
            human_players = players.filter(game=game, bot=False, guessed_out = False)
            if human_players.count() == 1:
                return redirect('winner_page',pk=pk)
                
            if not guess.correct:

                # it's the next player's turn now, unless they are a bot
                current_player.guessing = False
                current_player.save()
                if guessed_player.bot == False:
                    guesser = guessed_player
                else:
                    guesser = random.choice(human_players.exclude(name=current_player.name))
                guesser.guessing = True
                guesser.save()

            return redirect('view_result', pk=pk)
        
         # no guess was made, refresh button was pressed sojust refresh the page
        else:
            pass

    context = {
        'current_player': current_player,
        'guessing_player': guessing_player,
        'question': game.question,
        'game_id': pk,
        'chooseable_players': chooseable_players,
        'chooseable_answers': chooseable_answers
        }
    return render(request, 'dinner/guess.html', context)


@registration_required
def view_result(request,pk):

    # this is where players are directed if there a a result to view.
    # They will continue to be directed here untill all human players who are not guessed out have viewed it.

    # fetch the game and player objects
    game = get_object_or_404(Game, pk=pk) 
    players = Player.objects.filter(game=game)
    current_player = players.get(name=request.session['player_name'])

    # fetch the most recent guess
    most_recent_guess = Guess.objects.filter(game_id=pk).order_by('-id').first()

    # Once the results have been viewed, update the player has_viewed_result to True
    if request.method=='POST':
     
        # Recount the humans players. Check if only one player remains in the game & redirect to winner page if so.
        remaining_human_players = players.filter(game=game, bot=False, guessed_out=False )

        # Check if only one player remains in the game & redirect to winner page if so.
        if remaining_human_players.count() == 1:
            return redirect('winner_page',pk=pk)

        # if all remaining human players have viewed the result, we can go to guess page
        if not remaining_human_players.filter(has_viewed_result=False).exists():
            return redirect('guess',pk=pk)
        
        # also if none of the remaining human players have viewed if - this means that the next round has started and the player variables updated
        if not remaining_human_players.filter(has_viewed_result=True).exists():
            return redirect('guess',pk=pk)
        
    # otherwise render the form again but will display a holding message

    # acknowledge that the current plasyer has viewed the results
    current_player.has_viewed_result=True
    current_player.save()

    context = {
        'guesser': most_recent_guess.guesser,
        'correct': most_recent_guess.correct,
        'game': game,
        'guessed_player': most_recent_guess.player,
        'guessed_answer': most_recent_guess.answer
        }
    return render(request, 'dinner/result.html', context)


def spectate(request, pk):
   
    # fetch the game, question and player objects
    game = get_object_or_404(Game, pk=pk) 
    players = Player.objects.filter(game=game)
    current_player = players.get(name=request.session['player_name'])
    guessing_player = Player.objects.filter(guessing=True).first()

    # redirect to join page if the current game session is 'abandoned'
    if game.status == 'abandoned':
        return redirect('join_game')
    
    # redirect to winner page if current game session is 'finished'
    if game.status == 'finished':
        return redirect('join_game')
    
    # Fetch players who are not guessed out
    remaining_players = players.filter(guessed_out=False)
    
    # Fetch answers for the current game where the player is not guessed out
    answers = Answer.objects.filter(question__game=game)
    remaining_answers = answers.filter(player__guessed_out=False)
    
    context = {
        'current_player': current_player,
        'guessing_player': guessing_player,
        'question': game.question,
        'chooseable_players': remaining_players,
        'chooseable_answers': remaining_answers
            }

    return render(request, 'dinner/spectate.html', context)


@registration_required
def start_new_game(request):

    # retrieve current player from session data
    current_player = Player.objects.get(name=request.session['player_name'])

    # create a new game and store it's id in the session data
    game = Game.objects.create(
        host=current_player,
        status = 'get_question'
        )
    request.session['game']=game.pk

    # set all players to initial state
    players = Player.objects.all()
    players.update(has_viewed_result=False)

    #redirect to get the question
    return redirect('get_question', pk=game.pk)



def get_question(request, pk):

    # retrieve current player and game objects from session data
    current_player = Player.objects.get(name=request.session['player_name'])
    game = get_object_or_404(Game, pk=pk)

    # update the question object and game status
    if request.method == 'POST':
        question_form = QuestionForm(request.POST)
        if question_form.is_valid():          
            question = question_form.save(commit=False)
            question.game = game
            question.save()
            game.status = 'lobby'
            game.save()
            return redirect('ask_question', pk=game.pk)
        
    # render the question form
    else:
        question_form = QuestionForm()
    
    context = {
        'question_form': question_form,
        'current_player': current_player
    }
    return render(request, 'dinner/start_new_game.html', context)


@registration_required
def reset_game(request):

    # Retrieve the current game primary key from the session, and then the game
    pk = request.session['game']
    game = get_object_or_404(Game, pk=pk)

    # declare the game abandoned
    game.status = 'abandoned'
    game.save()

    # delete all models
    models = apps.get_models()
    for model in models:
        model.objects.all().delete()

    # redirect to landing page
    return redirect('join_game')


@registration_required
def winner_page(request, pk):

    # retrieve game and current player from session data; update game status
    game = get_object_or_404(Game, pk=pk)  
    players = Player.objects.filter(game=game)
    current_player = Player.objects.get(name=request.session['player_name'])

    # retrieve the remaining human player
    remaining_human_player = players.filter(game=game, bot=False, guessed_out=False ).first()

    # update the game status
    game.status = "finished"
    game.save()
    
    if request.method == 'POST':
        return redirect('start_new_game')
    else:
        context ={
            'game_id':pk,
            'winner':remaining_human_player,
            'current_player':current_player
            }
        return render(request, 'dinner/winner_page.html', context)

@registration_required
def loser_page(request, pk):

    # retrieve current player from session data
    current_player = Player.objects.get(name=request.session['player_name'])

    if request.method == 'POST':
        return redirect('join_game')
    else:
        return render(request, 'dinner/loser_page.html', {'current_player':current_player, 'game_id':pk})
 