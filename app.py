import os

from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError

import sqlite3


from helpers import usd, login_required, apology

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
conn = sqlite3.connect('bookStore.db')

# conn.execute('CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT NOT NULL, hash TEXT NOT NULL, cash NUMERICAL)')

@app.route("/")
def index():
    return render_template("index.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    
    # Forget any user_id
    session.clear()
    # user submitted the form
    if request.method == "POST":

        if not request.form.get("username"):
            return apology("username cannot be blank", 400)

        elif not request.form.get("password"):
            return apology("password cannot be blank")

        
        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page once logged in
        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    try:
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        with sql.connect("bookStore.db") as con:
            db = con.cursor()

            if username == "" or len(db.execute("SELECT username FROM users WHERE username = ?", username)) > 0:
                return apology("Invalid username: Blank, or already exists")
            if password == "" or password != confirmation:
                return apology("Invalid passowrd: Blank or password does not match")

            
            # adding user to the database
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, generate_password_hash(password))
            con.commit()
        
            rows = db.execute("SELECT * FROM users WHERE username = ?", username)

            # Logs user in and remembers that he/she has logged in
            session["user_id"] = rows[0]["id"]

            
    except:
        con.rollback()
    finally:
        return redirect("/")