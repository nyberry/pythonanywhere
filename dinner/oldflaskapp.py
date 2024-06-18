import random
import datetime

from cs50 import SQL
from flask import Flask, redirect, render_template, request, session
from flask_session import Session

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///dinner.db")

# global variables
question = "No question loaded"
host_id = None
guesser_name, next_guesser_name, guestguessed, answerguessed = None, None, None, None
gamephase = "not started"  # not started, lobby, live, round finished
eggtimer = None


def validate_username(username):
    # check a username was provided
    if not username:
        return None, "please provide name"
    if len(username) > 20:
        username = username[:20]
    # Ensure username does not already exist:
    username_existing_entry = db.execute("SELECT * FROM users WHERE username = ?", username)
    if len(username_existing_entry) != 0:
        print(username_existing_entry)
        return None, "username already in use"
    # Username is valid
    return username, None


def choose_question():
    # returns the most recent question from the group of least asked questions
    rows = db.execute("SELECT * FROM questions ORDER BY appearances, timestamp DESC;")
    print(rows)
    question = rows[0]["question"]
    appearances = rows[0]["appearances"]
    db.execute("UPDATE questions SET appearances = ? WHERE question = ?", appearances+1, question)
    return question


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
def index():
    # landing page when someone enters the URL (rather than following an invitation link)
    # this will usually be the host starting a game.

    global gamephase, host_id, question

    if request.method == "GET":
        return render_template("landing.html")

    if request.method == "POST":

        if gamephase == "not started":
            # create a fresh game table in the database
            db.execute("DELETE FROM users;")
            gamephase = "lobby"

            # Ensure a valid username was submitted
            username = request.form.get("username")
            username, error = validate_username(username)
            if error:
                return apology(f'{error}', 400)

            # add this user
            db.execute("INSERT INTO USERS (username, answer, guessed, status) VALUES (?, ?, ?, ?);",
                       username, "None", False, "not yet provided an answer")

            # Remember which user has logged in
            rows = db.execute("SELECT * FROM users WHERE username = ?", username)
            session["user_id"] = rows[0]["id"]

            # If there is no host yet, make this user the host
            if not host_id:
                host_id = session["user_id"]

            # Decide the queston for the game
            question = choose_question()

            # Redirect to the "send invitation" page
            return redirect("/invit")

        elif gamephase == "lobby":
            # a new game has already been started, so just add this user as a normal user

            # Ensure a valid username was submitted
            username = request.form.get("username")
            username, error = validate_username(username)
            if error:
                return apology(f'{error}', 400)

            # Add the user
            db.execute("INSERT INTO USERS (username, answer, guessed, status) VALUES (?, ?, ?, ?);",
                       username, None, False, "not yet provided an answer")
            print(f'{username} added')

            # Remember which user has logged in
            rows = db.execute("SELECT * FROM users WHERE username = ?", username)
            session["user_id"] = rows[0]["id"]

            # redirect them to the ask question page
            return redirect("/ask")

        else:
            # a game is in progress
            return apology("Whoops - a game is in progress", 400)


@app.route("/invit", methods=["GET", "POST"])
def invit():
    # This is the page to send out invitations to other users.
    if request.method == "GET":
        host = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
        host = host[0]["username"]
        invitation_text = f'{host} requests the pleasure of your company at the dinner party game: '
        return render_template("invit.html", invitation_text=invitation_text)

    else:
        # they have
        return redirect("/ask")


@app.route("/invitation", methods=["GET", "POST"])
def invitation():
    # This is the landing page for players responding to a whatsapp link.
    # if the game has not yet started (eg. they followed an old link) then send them to the host landing page
    if gamephase == "not started":
        return redirect("/")

    if request.method == "GET":
        return render_template("invitation.html")

    if request.method == "POST":

        # Ensure a valid username was submitted
        username = request.form.get("username")
        username, error = validate_username(username)
        if error:
            return apology(f'{error}', 400)

        # add the user
        db.execute("INSERT INTO USERS (username, answer, guessed, status) VALUES (?, ?, ?, ?);",
                   username, None, False, "not yet provided an answer")
        print(f'{username} added')

        # Remember which user has logged in
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        session["user_id"] = rows[0]["id"]

        # Redirect user to the question page
        return redirect("/ask")


@app.route("/ask", methods=["GET", "POST"])
def ask():
    # this asks the user for their answer to the question, and stores it.
    if request.method == "POST":
        answer = request.form.get("answer")
        user_id = session.get("user_id")
        db.execute("UPDATE USERS SET answer =?, status = ? WHERE id = ?", answer, 'provided answer', user_id)
        return redirect("/show_users")
    else:
        return render_template("ask.html", question=question)


@app.route("/show_users", methods=["GET", "POST"])
@login_required
def show_users():
    global gamephase, guesser_id, next_guesser_name
    if request.method == "POST":
        gamephase = "live"
        print(f'The host has pressed Go. Game phase: {gamephase}')

        # remove any players who have not provided an answer:
        rows = db.execute("SELECT username FROM users WHERE status = 'not yet provided an answer'")
        if rows:
            print(f'the following players {rows} have not provided an answer and will be removed from this game')
        else:
            print(f'all players provided an answer')
        db.execute("DELETE FROM users WHERE status = 'not yet provided answer'")

        # make sure there are at least 2 players:
        rows = db.execute("SELECT username FROM users")
        if len(rows) < 2:
            return apology("Must be at least 2 players")

        # update the guesser, if known
        if next_guesser_name:
            print(f"Next to guess will be: {next_guesser_name}")
        # otherwise randomly select who is going to play first
        else:
            players = db.execute("SELECT * FROM USERS")
            next_guesser_name = random.choice(players)['username']
            print(f"First to guess will be: {next_guesser_name}")
        return redirect("/show_answers")
    else:
        user_id = session.get("user_id")
        hoststatus = (user_id == host_id)       # true if host
        users = db.execute("SELECT * FROM USERS")
        usersStatus = []
        for row in users:
            answer = row["answer"]
            username = row["username"]
            usersStatus.append([username, "Yes" if answer else "No"])
        return render_template("/show_users.html", userlist=usersStatus, show_button=hoststatus)


@app.route('/update_hat')
@login_required
def update_hat():
    if gamephase == "lobby":
        """send list of current users + whether they have provided an answer"""
        users = db.execute("SELECT * FROM USERS")
        userlist = "<table><thead><tr><th>Guest</th><th>Submitted answer?</th></tr></thead><tbody>"
        for row in users:
            userlist += f"<tr><td>{row['username']}</td><td>{'Yes' if row['status']=='provided answer' else 'No'}</td></tr>"
        userlist += "</table>"
        return userlist
    else:
        user_id = session.get("user_id")
        print(f"The host has pressed 'Start Game', so rerouting user {user_id} to show_answers page")
        return "start game"


@app.route('/check_if_round_finished')
@login_required
def check_if_round_finished():
    global gamephase
    if gamephase == "round finished":
        return "true"
    else:
        return "false"


@app.route('/show_answers', methods=["GET", "POST"])
@login_required
def show_answers():
    if request.method == "GET":
        answers = db.execute("SELECT answer FROM USERS")
        answerlist = [row['answer'] for row in answers]
        random.shuffle(answerlist)
        return render_template("show_answers.html", question=question, answers=answerlist)
    elif request.method == "POST":
        user_id = session.get("user_id")
        print(f'User ID {user_id} has acknowledged and status should be set to "acknowledged"')
        db.execute("UPDATE USERS SET status = 'acknowledged' WHERE id = ?", user_id)
        status = db.execute("SELECT id, status FROM USERS")
        print(f"Status of users {status}")
        return redirect("/wait_for_next_round")


@app.route('/gameplay', methods=["GET", "POST"])
@login_required
def gameplay():
    global guesser_name, guestguessed, answerguessed, gamephase, question
    guesser_name = next_guesser_name
    user_id = session.get("user_id")
    user = db.execute("SELECT username FROM USERS WHERE id = ?", user_id)
    username = user[0]['username']
    print(f"gameplay route for user: {user}, {username}")

    if request.method == "GET":
        guestguessed = None
        guests = db.execute("SELECT username FROM USERS WHERE guessed = False")
        guestlist = [row['username'] for row in guests]
        if len(guestlist) == 1:
            question = None
            return redirect("/winner")

        random.shuffle(guestlist)
        print(f"Guest list: {guestlist}")
        return render_template("gameplay.html", question=question, guesser_name=guesser_name, guests=guestlist, guestguessed=False, answers=[], username=username)

    elif request.method == "POST":
        response1 = request.form.get("response1")
        if response1:
            guestguessed = response1
            answers = db.execute("SELECT answer FROM USERS WHERE guessed = False")
            answerlist = [row['answer'] for row in answers]
            random.shuffle(answerlist)
            return render_template("gameplay.html", question=question, guesser_name=guesser_name, guests=[], guestguessed=guestguessed, answers=answerlist, username=username)

        response2 = request.form.get("response2")
        if response2:
            answerguessed = response2
            gamephase = "round finished"
            return redirect("/show_round")

        return apology("Something custard")


@app.route('/winner', methods=["GET", "POST"])
@login_required
def winner():
    global gamephase, question
    user_id = session.get("user_id")
    user = db.execute("SELECT username FROM USERS WHERE id = ?", user_id)
    username = user[0]['username']

    if request.method == "GET":
        row = db.execute("SELECT username FROM USERS WHERE guessed = False")
        print(f'winner row {row}')
        winner = row[0]['username']
        winnertext = winner + " wins!" if winner != username else "You win!"
        return render_template("winner.html", winnertext=winnertext)

    if request.method == "POST":
        new_question = request.form.get("question")
        if new_question:
            current_time = datetime.datetime.now()
            timestamp = current_time.timestamp()
            db.execute("INSERT INTO QUESTIONS (question, timestamp, author, appearances) VALUES (?, ?, ?, ?)",
                       new_question, timestamp, username, 0)
        db.execute("UPDATE USERS SET answer = ?, status = ?, guessed = ? WHERE id = ?",
                   None, 'not yet provided an answer', False, user_id)
        gamephase = "lobby"
        if not question:
            question = choose_question()
        return redirect("/ask")


@app.route('/show_round', methods=["GET", "POST"])
@login_required
def show_round():
    global next_guesser_name
    user_id = session.get("user_id")
    user = db.execute("SELECT username FROM USERS WHERE id = ?", user_id)
    username = user[0]['username']

    if request.method == "GET":
        db.execute("UPDATE USERS SET status = 'not yet acknowledged' WHERE id = ?", user_id)
        displayguesser = guesser_name if guesser_name != username else "You"
        displayguessee = guestguessed+"'s" if guestguessed != username else "your"
        row = db.execute("SELECT answer FROM USERS WHERE username = ?", guestguessed)
        correctanswer = row[0]['answer']
        result = "CORRECT" if answerguessed == correctanswer else "WRONG"
        if result == "CORRECT":
            db.execute("UPDATE USERS SET guessed = True WHERE username = ?", guestguessed)
            print(f"{guestguessed} is out")
        if result == "WRONG":
            # select who is going to play next
            row = db.execute("SELECT username FROM USERS WHERE username = ?", guestguessed)
            next_guesser_name = row[0]['username']
            print(f"Next to guess will be: {next_guesser_name}")
        return render_template("show_round.html", question=question, guesser_name=displayguesser, answerguessed=answerguessed, guestguessed=displayguessee, result=result)

    elif request.method == "POST":
        print(f'User ID {user_id} has acknowledged and status should be set to "acknowledged"')
        db.execute("UPDATE USERS SET status = 'acknowledged' WHERE id = ?", user_id)
        status = db.execute("SELECT id, status FROM USERS")
        print(f"Status of users {status}")
        return redirect("/wait_for_next_round")


@app.route('/wait_for_next_round')
@login_required
def wait_for_next_round():
    unfinished = db.execute("SELECT id, status FROM USERS WHERE status != 'acknowledged' and guessed = False")
    if unfinished:
        return render_template("wait_for_next_round.html")
    else:
        return redirect("/gameplay")

@app.route('/check_all_users_have_acknowledged')
@login_required
def check_all_users_have_acknowledged():
    global gamephase, eggtimer
    unfinished = db.execute("SELECT id, status FROM USERS WHERE status != 'acknowledged' and guessed = False")
    if unfinished:
        print(f"The following users have not acknowledged: {unfinished}")
        if eggtimer == None:
            eggtimer = datetime.datetime.now()
            return "false"
        else:
            time_difference =  datetime.datetime.now()-eggtimer
            if time_difference.total_seconds() >= 5:
                print (f"Not all users acknowledged, but we moved on anyway")
                reset_eggtimer()
                return "true"
            else:
                return "false"
    else:
        print(f"All users have acknowledged")
        reset_eggtimer()
        return "true"

def reset_eggtimer():
    global gamephase, eggtimer
    gamephase = "live"
    eggtimer = None
    # db.execute("UPDATE users SET answer = ?, guessed = ? , status = ?", None, False, "not yet provided an answer")
    return

if __name__ == "__main__":
    app.run()