from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.db.models import Max
from .models import Player, Game, Question, Answer, Guess
from .forms import QuestionForm, AnswerForm
from .helpers import registration_required, log_in, log_out, custom_404, reset_game, shuffle_answers, create_bots
from django.db import IntegrityError
import random
from random import shuffle

# minimum numeber of players - bots will be created
MIN_PLAYERS = 6

@registration_required
def front_door(request):

    # This is the landing page immediately after a player registers

    if request.method == "POST":
        return redirect('join_game')

    # Load the player data
    players = Player.objects.all()
    current_player = players.get(name=request.session['player_name'])
    other_players = players.exclude(name = current_player.name)

    # Check if there are any games. If not, invite the user to start a game
    games = Game.objects.all()
    if not games:
        return render(request, 'dinner/welcome.html', {'other_players':other_players, 'current_player':current_player, 'game':None})

    # else, load the most recent game and invote the player to join it at the appropriate route
    most_recent_game_id = games.aggregate(Max('id'))['id__max']
    game = get_object_or_404(Game, pk=most_recent_game_id)
    return render(request, 'dinner/welcome.html', {'other_players':other_players, 'current_player':current_player, 'game':game})


@registration_required
def join_game(request):

    # This is the landing page for registered players. If there are no games, create a game now.
    games = Game.objects.all()
    if not games:
        return redirect('start_new_game')

     # Load the most recently created game & store its id in the session data
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
    elif game.status == "guessing" or game.status == "viewing_result":
         return redirect(reverse('spectate', kwargs={'pk': most_recent_game_id}))
    
     # if the game has finished status, direct the player to the wait_for_question page
    elif game.status == "finished":
        current_player = Player.objects.get(name=request.session['player_name'])
        winner = Player.objects.filter(game=game, guessed_out=False)[0]
        return render(request,'dinner/wait_for_question.html',{'host':winner.name, 'current_player':current_player})
    
    print (f'game status {game.status}')



@registration_required
def ask_question(request, pk):
    # This is the page where players are asked a question, and then they are sent to the lobby

    # Load the game object
    game = get_object_or_404(Game, pk=pk)
    
    # Fetch and initialise the current player object from session data
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

    # Check if the current player has already answered this question. If so, redirect to lobby
    has_answered = answers.filter(player=current_player).exists()
    if has_answered:
        return redirect(reverse('lobby', kwargs={'pk': pk}))

    # If the form has been returned by POST method
    if request.method == "POST":

        form = AnswerForm(request.POST)
        
        if form.is_valid():
            answer = form.save(commit=False)
            answer.question = question
            answer.player = current_player
            answer.display_order = 0 
            try:
                answer.save()
                print ("answer saved")
            except IntegrityError:
                form.add_error(None, "You have already answered this question.")
            return redirect(reverse('lobby', kwargs={'pk': pk}))

    # render the form to get question
        
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
            game.status ="guessing"
            game.save()

            # Call the function to add some bot players
            create_bots(MIN_PLAYERS,pk)

            # Call the function to shuffle the answers
            shuffle_answers()

            # Select a random player to be the guesser, and set all the others to not be guessers
            players = Player.objects.filter(game=pk)
            players.update(guessing = False)
            human_players = players.filter(bot=False)
            guesser = random.choice(human_players)
            guesser.guessing = True
            guesser.save()

    # redirect to guess page if the current game session is now active
    if game.status == 'guessing':
        return redirect('guess', pk=pk)

    # redirect to join page if the current game session is not lobby
    elif game.status != 'lobby':
        return redirect('join_game')
    
    # fetch the players who have answered the current question, and render the lobby page
    current_question = get_object_or_404(Question, game=game)
    players = Player.objects.filter(game=game)
    current_player = players.get(name=request.session['player_name'])
    players_with_answers = players.filter(answer__question=current_question).distinct()
    players_without_answers = players.exclude(id__in=players_with_answers.values_list('id', flat=True))

    context = {
        'game_id': pk,
        'question': game.question,
        'players_with_answers': players_with_answers,
        'players_without_answers': players_without_answers,
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

    # redirect to the results route if the game status requires
    if game.status == 'viewing_result':
        print (f'redirecting {current_player} to see the results')
        return redirect('view_result',pk=pk)
    
    # Fetch chooseable players
    remaining_players = players.filter(guessed_out=False)
    chooseable_players = list(remaining_players.exclude(id=current_player.id))
 
    # Fetch the sorted list of choosable answers
    answers = Answer.objects.filter(question__game=game).order_by('display_order')
    remaining_answers = answers.filter(player__guessed_out=False)
    chooseable_answers = list(remaining_answers.exclude(player__id=current_player.id))

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

            game.status = "viewing_result"
            game.save()

            return redirect('view_result', pk=pk)

    # render the guess page

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
def view_result(request, pk):

    # this is where players are directed if there a a result to view.
    # They will continue to be directed here until remaining players have acknowledged

    # fetch the game object
    game = get_object_or_404(Game, pk=pk)

    # if all players have acnowledged the result, go back to guessing
    if game.status == 'guessing':
        return redirect('guess',pk=pk)
    
    # fetch the most recent guess object
    guesses = Guess.objects.all()
    most_recent_guess_id = guesses.aggregate(Max('id'))['id__max']
    guess = get_object_or_404(Guess, pk=most_recent_guess_id)

    # fetch the player objects
    players = Player.objects.filter(game=game)
    current_player = players.get(name=request.session['player_name'])
    remaining_human_players = players.filter(game=game, bot=False, guessed_out=False )

    # Winner?
    remaining_human_players = players.filter(game=game, bot=False, guessed_out=False )
    if remaining_human_players.count() == 1:
        players.update(has_acknowledged_winner=False)
        return redirect('winner_page',pk=pk)

    # Once the results have been viewed, the player clicks OK to return here:
    if request.method=='POST':

        # process the actual guess, if this player has made it
        if current_player == guess.guesser:
  
            # Is a player out?
            if guess.correct:
                guess.player.guessed_out = True
                guess.player.save()
                        
            # Now a winner?
            remaining_human_players = players.filter(game=game, bot=False, guessed_out=False )
            if remaining_human_players.count() == 1:
                players.update(has_acknowledged_winner=False)
                return redirect('winner_page',pk=pk)
                    
            # Change guesser if not correct
            if not guess.correct:
                
                current_player.guessing = False
                current_player.save()

                if guess.player.bot == False:
                    guesser = guess.player

                else:
                    eligible_players = remaining_human_players.exclude(name=current_player.name)
                    guesser = random.choice(eligible_players)
                    guesser.guessing = True
                    guesser.save()

        # is the current player out? (They still need to acknowledge the result)
        print (f'Current player guesswd out?{current_player.guessed_out}')
        if current_player.guessed_out == True:
            return redirect ('loser_page',pk=pk)

        # acknowledge that the current player has viewed the results
        current_player.has_acknowledged_result=True
        current_player.save()
        print (f'{current_player} has just acknowledged the result')

        # if all remaining human players have viewed the result, reset status
        if not remaining_human_players.filter(has_acknowledged_result=False).exists():
            remaining_human_players.update(has_acknowledged_result = False)
            game.status= 'guessing'
            game.save()

        if game.status == 'guessing':
            return redirect('guess',pk=pk)
        
    # Render the form to show result
    
    answers = Answer.objects.filter(question__game=game).order_by('display_order')

    context = {
        'current_player': current_player,
        'players': players,
        'answers' : answers,
        'guesser': guess.guesser,
        'correct': guess.correct,
        'game': game,
        'guessed_player': guess.player,
        'guessed_answer': guess.answer
        }
    return render(request, 'dinner/result.html', context)


def spectate(request, pk):
   
    # fetch the game, question and player objects
    game = get_object_or_404(Game, pk=pk) 
    players = Player.objects.filter(game=game)
    current_player = players.get(name=request.session['player_name'])
    guessing_player = Player.objects.filter(guessing=True).first()

    # redirect to winner page if current game session is 'finished'
    if game.status == 'finished':
        return redirect('winner_page')
    
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

    # get players objects
    players = Player.objects.all()

    # delete old bots
    for player in players:
        if player.bot == True:
            player.delete()

    # set players to initial state
    for player in players:
        print (f'Players: {players}')
    players.update(has_acknowledged_result=False)
    players.update(has_acknowledged_winner=True)

    # refresh models
    Question.objects.all().delete()
    Answer.objects.all().delete()
    Guess.objects.all().delete()

    #debugging
    print (f'Starting a new game {game.pk} with:')
    print (f'host: {game.host}')
    for player in players:
        print (f'player: {player.name}')


    #redirect to get the question
    return redirect('get_question', pk=game.pk)



@registration_required
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
def winner_page(request, pk):

    # retrieve game and player objects
    game = get_object_or_404(Game, pk=pk)  
    human_players = Player.objects.filter(game=game, bot=False)
    current_player = Player.objects.get(name=request.session['player_name'])
    winner = human_players.filter(guessed_out=False ).first()

    print (f'game = {game.pk}')
    print (f'winner = {winner.name}')
    print (f'game_status = {game.status}')

    # Confirmation form post
    if request.method == 'POST':

        # acknowledge that the winning player has viewed the results
        current_player.has_acknowledged_winner=True
        current_player.save()

        # if all human players have viewed the result, reset status
        if not human_players.filter(has_acknowledged_winner=False).exists():
            game.status = "finished"
            game.host = winner
            game.save()

        for player in human_players:
            print(player.name, "acknowledged winner?", player.has_acknowledged_winner)

    if game.status == 'finished':
   
        # if current player is winner, redirect to start new game
        if current_player == winner:
            return redirect('start_new_game')
        
        # otherwise, redirect to wait for question
        else:
            return redirect('join_game')
    
    # render the winner acknowledgement form
    context ={
        'game_id':pk,
        'winner':winner,
        'current_player':current_player
        }
    return render(request, 'dinner/winner_page.html', context)

@registration_required
def loser_page(request, pk):

    # retrieve current player from session data
    current_player = Player.objects.get(name=request.session['player_name'])

    if request.method == 'POST':
        
        # acknowledge that the current player has viewed the results
        current_player.has_acknowledged_result=True
        current_player.save()
    
        # redirect them to spectate
        return redirect('join_game')
    
    # render loser page
    return render(request, 'dinner/loser_page.html', {'current_player':current_player, 'game_id':pk})
 