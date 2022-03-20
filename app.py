import os

from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError

import pymysql


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
# connection = pymysql.connect(host="localhost",user="root",passwd="",database="bookStore" )
# db = connection.cursor()

@app.route("/")
def index():
    return render_template("index.html")



@app.route("/login")
def login():
    return render_template("login.html")