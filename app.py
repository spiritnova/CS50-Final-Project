import os
import re

from flask import Flask, redirect, render_template, request, session, g
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError

from cs50 import SQL

from bs4 import BeautifulSoup
from helpers import usd, login_required

from datetime import datetime

app = Flask(__name__)


# Ensures templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensures responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#database connection
db = SQL("sqlite:///bookStore.db")


@app.route("/")
def index():
    return render_template("index.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    # Function reponsible for logging the user in

    # Forget any user_id
    session.clear()
    # user submitted the form
    if request.method == "POST":

        if not request.form.get("username"):
            return render_template("apology.html", message="username cannot be blank")

        elif not request.form.get("password"):
            return render_template("apology.html", message="password cannot be blank")

        username = request.form.get("username")
        password = request.form.get("password")

        # Query database for username
        rows = db.execute("SELECT * FROM users where username = ?", username)
        

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return render_template("apology.html", message="invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        session["username"] = rows[0]["username"]

        # redirect user to home page once logged in
        return redirect("/")

    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    # Logs user out

    # Forget the user id from session

    session.clear()

    # Redirect user to login form
    return redirect("/login")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirmation = request.form["confirmation"]

        if username == "":
            return render_template("apology.html", message="Invalid username")
        if len(db.execute("SELECT username FROM users where username =?", username)) > 0:
            return render_template("apology.html", message="Username already exists")
        if password == "":
            return render_template("apology.html", message="Password cannot be blank")
        if password != confirmation:
            return render_template("apology.html", message="Password do not match")
        # Password rules
        pattern = re.compile("^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$")
        if not pattern.match(request.form.get("password")):
            return render_template("apology.html", message="Password must at least have a minimum of 8 characters, at least one letter, one number and a one special character")
                
        # adding user to the database
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, generate_password_hash(password) )
    
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Logs user in and remembers that he/she has logged in
        session["user_id"] = rows[0]["id"]

        return redirect("/")

@app.route("/profile/")
@login_required
def profile():
    return redirect("/profile/edit")

@app.route("/profile/edit")
@login_required
def profile_edit():
    return render_template("profileEdit.html")

@app.route("/profile/password/change")
@login_required
def profile_password_change():
    return render_template("passwordChange.html")

@app.route("/profile/wallet")
@login_required
def profile_wallet():
    user_id = session["user_id"]
    cash = db.execute("SELECT cash FROM users where id=?", user_id)[0]["cash"]
    return render_template("profileWallet.html", cash=cash)


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")

