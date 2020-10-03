import os 

from flask import Flask, render_template, request, flash, redirect, session, g, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from secret import API_SECRET_KEY
from models import db, connect_db, User, Recipe
from sqlalchemy.exc import IntegrityError
from forms import UserAddForm, LoginForm

#remove this eventually
CURR_USER_KEY = "curr_user"

app = Flask(__name__)

#Get DB_URI from environ variable or, if not set there, user development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgres:///usemyfood_db'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = API_SECRET_KEY
# app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
toolbar = DebugToolbarExtension(app)

connect_db(app)

########
#User signup/login/logout

@app.before_request
def add_user_to_g():
    """If logged in, add curr user to Flask global, not sure if this works for multiple uses"""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None 

def do_login(user):
    """Log in user"""

    session[CURR_USER_KEY] = user.id  

def do_logout():
    """Logout user"""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Create new user and add to DB. Then redirect home.
    If the form is not valid, present form.
    Flash a message and re-present form is user with that username already
    """
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
            )
            db.session.commit()
        
        except IntegrityError as e:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)
        
        do_login(user)

        return redirect("/")
    
    else:
        return render_template('users/signup.html', form=form)

@app.route("/logout")
def logout():
    """Handle logging out a user."""

    do_logout()

    flash("You have been logged out, enjoy your meal!", 'success')
    return redirect('/')

@app.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login"""

    form = LoginForm()


    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}, let's get cooking!", 'success')
            return redirect('/')
        
        flash("Invalid credentials.", 'danger')
    
    return render_template('users/login.html', form=form)

##############################################################
# Basic user routes:

@app.route('/users/<int:user_id>')
def user_details(user_id):
    """Show a users detail page"""

    user = User.query.get_or_404(user_id)

    return render_template("users/details.html", user=user)


@app.route('/users/<int:user_id>/favorites')
def user_favorites(user_id):
    """Display a list of the users favorites"""

    user = User.query.get_or_404(user_id)
    
    return render_template('users/favorites.html', user=user)


@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete a user's account"""

    if not g.user:
        flash("Access unauthorized", 'danger')
    
    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect('/signup')

##############################################################





###############################################################
#Home page and error pages

@app.route('/')
def homepage():
    """Show homepage, will need to have validation added"""
    return render_template('home.html')



@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
