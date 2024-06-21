from django.shortcuts import render, get_object_or_404, redirect
from .models import Player, Game, Question, Answer, Guess
from .forms import QuestionForm, AnswerForm, GuessForm, PlayerRegistrationForm
from .helpers import registration_required
from django.db import IntegrityError

def register_player(request):
    if request.method == 'POST':
        form = PlayerRegistrationForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            if Player.objects.filter(name=name).exists():
                return render(request, 'registration/welcome.html', {'form': form})        
            Player.objects.create(name=name)
            request.session['player_name'] = name
            return redirect('game_list') 
    else:
        form = PlayerRegistrationForm()
        return render(request, 'registration/welcome.html', {'form': form})


def game_list(request):
    games = Game.objects.all()
    return render(request, 'dinner/game_list.html', {'games': games})
    

@registration_required
def game_detail(request, pk):
    game = get_object_or_404(Game, pk=pk)

    # Fetch the current player object from sessionlayer
    players = Player.objects.all()
    current_player = Player.objects.get(name=request.session['player_name'])
    current_player.game = game
    current_player.guessed_out= False
    current_player.save()
    
    # Fetch the current game question and the answers given so far
    question = game.question 
    answers = Answer.objects.filter(question=question)
    
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
            return redirect('game_detail', pk=game.pk)
    else:
        form = AnswerForm()
    return render(request, 'dinner/game_detail.html', {'game': game, 'question': question, 'answers': answers, 'form': form, 'players':players})


@registration_required
def guess(request, pk):
    game = get_object_or_404(Game, pk=pk)
    answers = Answer.objects.filter(question__game=game)
    players = Player.objects.filter(game=game)
    remaining_players = Player.objects.filter(game=game, guessed_out=False)
    remaining_answers = Answer.objects.filter(question__game=game, player__guessed_out=False) 
    current_player = Player.objects.get(name=request.session['player_name'])
    if current_player.guessed_out==True:
         return redirect('loser_page',pk=pk)
       
    if request.method == "POST":
        form = GuessForm(request.POST,remaining_answers=remaining_answers, remaining_players=remaining_players)
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
                    return redirect('winner_page',pk=pk)

            return render(request, 'dinner/result.html', {'correct': guess.correct, 'game': game, 'guessed_player': guessed_player, 'guessed_answer': guessed_answer})
           
    else:
        form = GuessForm(remaining_answers=remaining_answers, remaining_players=remaining_players)
    
    return render(request, 'dinner/guess.html', {'form': form, 'game': game, 'answers': answers, 'players':players, 'remaining_answers': remaining_answers, 'remaining_players':remaining_players})


@registration_required
def add_question(request):
    if request.method == "POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('game_list')
    else:
        form = QuestionForm()
    return render(request, 'dinner/add_question.html', {'form': form})

@registration_required
def start_new_game(request):
    current_player = Player.objects.get(name=request.session['player_name'])

    if request.method == 'POST':
        question_form = QuestionForm(request.POST)
        if question_form.is_valid():        
            game = Game.objects.create(creator=current_player)   
            question = question_form.save(commit=False)
            question.game = game
            question.save()
            current_player.guessed_out = False
            current_player.save()
            return redirect('game_detail', pk=game.pk)
    else:
        question_form = QuestionForm()
    
    context = {
        'question_form': question_form,
    }
    return render(request, 'dinner/start_new_game.html', context)

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