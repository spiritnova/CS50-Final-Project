import os
import re
import json
import requests

from flask import Flask, redirect, render_template, request, session, g
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.utils import secure_filename
import uuid as uuid
from urllib.request import urlopen

from cs50 import SQL

from bs4 import BeautifulSoup
from helpers import *

from datetime import datetime

bookapi = "https://www.googleapis.com/books/v1/volumes?q="

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


# Creating the User table
db.execute("CREATE TABLE IF NOT EXISTS users ( \
    id       INTEGER   PRIMARY KEY, \
    username TEXT      NOT NULL, \
    email    VARCHAR(100), \
    hash     TEXT      NOT NULL, \
    cash     NUMERICAL DEFAULT (1000), \
    picture  STRING      DEFAULT [pfp.png], \
    gender   TEXT      DEFAULT[none] \
);")

# Creating a table to keep track of bought books

db.execute("CREATE TABLE IF NOT EXISTS transactions ( \
    id          INTEGER, \
    user_id     NUMERIC NOT NULL, \
    book_id     INTEGER, \
    book_title  NOT NULL, \
    book_amount NUMERIC NOT NULL, \
    price       NUMERIC NOT NULL, \
    time TEXT, \
    PRIMARY KEY(id), FOREIGN KEY (user_id) \
        REFERENCES users(id), \
        FOREIGN KEY(book_id) REFERENCES bookList(book_id) );")


db.execute("CREATE TABLE IF NOT EXISTS bookList ( \
    book_id     INTEGER, \
    title  VARCHAR(255) NOT NULL, \
    author TEXT NOT NULL, \
    genre TEXT NOT NULL, \
    publishedDate NUMERIC NOT NULL, \
    price NUMERIC NOT NULL, \
    rating DECIMAL(4, 2) NOT NULL, \
    PRIMARY KEY(book_id) \
);")


# TEMP CART DB
db.execute("CREATE TABLE IF NOT EXISTS cart ( \
    user_id INTEGER NOT NULL, \
    title VARCHAR(255) NOT NULL, \
    price NUMERIC, \
    picture STRING, \
    FOREIGN KEY(user_id) REFERENCES users(id) \
)")


# Create a picture folder directory variable
picFolder = "./static/pictures/"
app.config['picFolder'] = picFolder



@app.route("/", methods=["POST", "GET"])
def index():
    api_key = "AIzaSyAUjIe6CgPoD9FGgxEDbwZvWdBeZj3Mxks"
    os.environ.get("API_KEY")
    if request.method == "POST":

        if not request.form.get("title"):
            return render_template("apology.html", message="title cannot be blank")

        book = request.form.get("title")

        url = f"https://www.googleapis.com/books/v1/volumes?q={book}&printType=books&maxResults=20&:keyes&key={api_key}"

        response = requests.get(url)

        data = response.json()
        
        return render_template("bookList.html", books=data["items"])

    # Get books from db

    rows = db.execute("SELECT title, picture from bookList where genre like ?", "%" + "Science-Fiction" + "%")
    rows_H = db.execute("SELECT title, picture from bookList where genre like ?", "%" + "horror" + "%")
    rows_R = db.execute("SELECT title, picture from bookList where genre like ? LIMIT 10", "%" + "Romance" + "%")
    rows_F = db.execute("SELECT title, picture from bookList where genre like ? LIMIT 10", "%" + "fantasy" + "%")

    return render_template("index.html", rows=rows, rows_H=rows_H, rows_R=rows_R, rows_F=rows_F)



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
        session["picture"] = rows[0]["picture"]
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

@app.route("/profile")
@login_required
def profile():
    user_id = session["user_id"]
    username = db.execute("SELECT username from users where id =?", user_id)[0]["username"]
    email = db.execute("SELECT email from users where id =?", user_id)[0]["email"]
    gender = db.execute("SELECT gender from users where id =?", user_id)[0]["gender"]
    return render_template("profile.html", username=username, email=email, gender=gender)

@app.route("/profile/edit", methods=["POST", "GET"])
@login_required
def profile_edit():
    user_id = session["user_id"]
    if request.method == "POST":

        # Handling gender now
        gender = request.form.get("gender")

        if int(gender) == 1:
            setGender = "Male"
        elif int(gender) == 2:
            setGender = "Female"
        elif int(gender) == 3:
            setGender = "Prefer not to say"
        else:
            setGender = "None"
        db.execute("UPDATE users SET gender=? where id=?", setGender, user_id)

        # Handling the email
        email = request.form.get("email")

        pattern = re.compile("^(.+)@(.+)$")
        if not pattern.match(email):
            return render_template("apology.html", message="Please enter a valid email")

        db.execute("UPDATE users SET email=? where id=?", email, user_id)


        # Handling the username
        username = request.form.get("username")
        db.execute("UPDATE users SET username=? where id=?", username, user_id)

        return redirect("/profile/edit")    
    return render_template("profileEdit.html")

@app.route("/profile/password/change")
@login_required
def profile_password_change():
    return render_template("passwordChange.html")

@app.route("/profile/wallet", methods=["POST", "GET"])
@login_required
def profile_wallet():
    user_id = session["user_id"]
    cash = db.execute("SELECT cash FROM users where id=?", user_id)[0]["cash"]
    if request.method == "POST":

        addCash = request.form.get("cashValue")

        if not addCash:
            return render_template("apology.html", message="Please enter a valid cash | Not Blank")

        if int(addCash) < 5:
            return render_template("apology.html", message="Please enter an amount greated than $5")
        total = cash + int(addCash)

        db.execute("UPDATE users SET cash =? where id =?", total, user_id)

        return redirect("/profile/wallet")
    return render_template("profileWallet.html", cash=cash)

@app.route("/profile/language")
@login_required
def profile_language():
    user_id = session["user_id"]
    return render_template("language.html")


@app.route("/profile/edit/image", methods=["POST", "GET"])
@login_required
def profilePictureChangeHandler():
    user_id = session["user_id"]
    if request.method == "POST":

        pic = request.files["picture"]

        if not pic:
            return render_template("apology.html", message="Failed to Submit blank file")

        # The code below grabs the name of the picture
        pic_filename = secure_filename(pic.filename)

        # Set UUID
        pic_name = str(uuid.uuid1()) + "_" + pic_filename

        # saving the image
        saver = request.files["picture"]

        saver.save(os.path.join(app.config['picFolder'], pic_name))

        # Changing it to string to save it in the db
        pic = pic_name

        db.execute("UPDATE users SET picture=? WHERE id=?", pic, user_id)
        return redirect("/profile/edit")
    return render_template("/profile/edit")


@app.route("/readmore/<genre>")
def readmoreSciFi(genre):

    genres = genre # Used to change the title of the page dynamically
    rows = db.execute("SELECT * from bookList WHERE genre LIKE ?", "%" + genre + "%")
    return render_template("readmore.html", rows=rows, genre=genres)


@app.route("/books", methods=["POST", "GET"])
def books():
    if request.method == "POST":
        title = request.form.get("search")
        if title:
            searchedTitle = db.execute("SELECT * from bookList where title LIKE ?", "%" + title + "%")
            return render_template("books.html", rows=searchedTitle)
        if not title:
            return render_template("apology.html", message="Title cannot be blank")

    rows = db.execute("SELECT * from bookList")
    return render_template("books.html", rows=rows)

@app.route("/books/select", methods=["POST","GET"])
def genreSelect():
    if request.method == "POST":

        genre = request.form.get("genreSelect") 

        if int(genre) == 1:
            rowsA = db.execute("SELECT * from bookList where genre like ?", "%" + "Action" + "%")
            return render_template("books.html", rows=rowsA)
        elif int(genre) == 2:
            rowsAd = db.execute("SELECT * from bookList where genre like ?", "%" + "Adventure" + "%")
            return render_template("books.html", rows=rowsAd)
        elif int(genre) == 3:
            rowsS = db.execute("SELECT * from bookList where genre like ?", "%" + "Science-Fiction" + "%")
            return render_template("books.html", rows=rowsS)
        elif int(genre) == 4:
            rowsH = db.execute("SELECT * from bookList where genre like ?", "%" + "Horror" + "%")
            return render_template("books.html", rows=rowsH)
        elif int(genre) == 5:
            rowsR = db.execute("SELECT * from bookList where genre like ?", "%" + "Romance" + "%")
            return render_template("books.html", rows=rowsR)
        elif int(genre) == 6:
            rowsF = db.execute("SELECT * from bookList where genre like ?", "%" + "Fantasy" + "%")
            return render_template("books.html", rows=rowsF)
        elif int(genre) == 7:
            rowsB = db.execute("SELECT * from bookList where genre like ?", "%" + "Biography" + "%")
            return render_template("books.html", rows=rowsB)
        elif int(genre) == 8:
            rowsfi = db.execute("SELECT * from bookList where genre like ?", "%" + "Fiction" + "%")
            return render_template("books.html", rows=rowsfi)
        elif int(genre) == 9:
            rowsT = db.execute("SELECT * from bookList where genre like ?", "%" + "Thriller" + "%")
            return render_template("books.html", rows=rowsT)
        elif int(genre) == 10:
            rowsC = db.execute("SELECT * from bookList where genre like ?", "%" + "Comedy" + "%")
            return render_template("books.html", rows=rowsC)
        elif int(genre) == 11:
            rowsP = db.execute("SELECT * from bookList where genre like ?", "%" + "Psychological" + "%")
            return render_template("books.html", rows=rowsP)
        elif int(genre) == 12:
            rowsD = db.execute("SELECT * from bookList where genre like ?", "%" + "Drama" + "%")
            return render_template("books.html", rows=rowsD)
        elif int(genre) == 13:
            rowsCr = db.execute("SELECT * from bookList where genre like ?", "%" + "Crime" + "%")
            return render_template("books.html", rows=rowsCr)
        elif int(genre) == 14:
            rowsDef = db.execute("SELECT * from bookList")
            return render_template("books.html", rows=rowsDef)


    rows = db.execute("SELECT * from bookList")
    return render_template("books.html", rows=rows)


@app.route("/buy/<title>/<price>/<picture>")
# @login_required
def buy(title, price, picture):

    user_id = session["user_id"]

    # adding to the cart db
    db.execute("INSERT INTO cart (title, price, picture,  user_id) VALUES(?, ?, ?, ?)", title, price, picture, user_id)

    return ('', 204)


@app.route("/cart")
@login_required
def cart():

    user_id = session["user_id"]

    # Get items from the cart
    items = db.execute("SELECT * from cart where user_id=?", user_id)

    

    return render_template("cart.html", rows=items)

@app.route("/cart/remove/<title>")
def cartRemove(title):
    user_id = session["user_id"]

    # Remove items from database
    remove = db.execute("DELETE from cart where title=? and user_id=?", title, user_id)

    return redirect("/cart")

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")



