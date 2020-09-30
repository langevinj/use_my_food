import os 
from flask import Flask, render_template, request, flash, redirect, session, g, jsonify
from flask_debugtoolbar import DebugToolbarExtension

from models import db, connect_db

#remove this eventually
CURR_USER_KEY = "curr_user"

app = Flask(__name__)

#Get DB_URI from environ variable or, if not set there, user development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgres:///usemyfood_db'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
toolbar = DebugToolbarExtension(app)

connect_db(app)
















###############################################################
#Home page and error pages

@app.route('/')
def homepage():
    """Show homepage, will need to have validation added"""
    return render_template('home.html')



@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
