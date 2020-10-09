import os 
import requests

from flask import Flask, render_template, request, flash, redirect, session, g, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from secret import API_SECRET_KEY
from models import db, connect_db, User, Favorites, Recipe, toggle_favorites
from sqlalchemy.exc import IntegrityError
from forms import UserAddForm, LoginForm, RecipeRatingForm

#remove this eventually
CURR_USER_KEY = "curr_user"

BASE_URL = "http://127.0.0.1:5000"

app = Flask(__name__)
#Get DB_URI from environ variable or, if not set there, user development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgres:///usemyfood_db'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('API_SECRET_KEY', "it's a secret")
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
#Basic favorites routes

@app.route('/users/curruser/favorites')
def return_list_favorites():
    """Return a list of the current user's favorites' recipe api_id"""
    favIds = []
    favorites = g.user.favorites

    for favorite in favorites:
        favIds.append(favorite.recipe.api_id)
    
    return {"favIds":favIds}

@app.route('/users/toggle_favorite', methods=["POST"])
def add_favorite():
    """Toggle a user's favorite, respond to JS with favorited or unfavorited"""
    if not g.user:
        flash("Access unauthorized", 'danger')
    
    id = request.json['id']
    response = toggle_favorites(id, g.user.id)
    
    return response

##############################################################
#Searching by recipe
@app.route('/search', methods=["POST"])
def search_by_recipe():
    """Request recipe information based on the title of the searched recipe"""
    search_term = request.form['searchRecipeTerm']

    #change the number here to change the amount of recipes returned, then search for recipes by recipe name
    payload = {'query': search_term, 'number': 2, 'addRecipeInformation': 'true', 'apiKey': API_SECRET_KEY}
    resp = requests.get('https://api.spoonacular.com/recipes/complexSearch', params=payload)

    search_results = resp.json()['results']

    #clean up all the information not needed
    recipe_list = json_to_recipe(search_results)

    return render_template('search/searchresults.html', search_term=search_term, recipe_list=recipe_list)


def json_to_recipe(recipes):
    """Clean up a list of json recipes into a simpler recipe list of objects"""
    recipe_list = []
    for recipe in recipes:
        # new_recipe = jsonify(name=recipe['title'], recipe_url=recipe['sourceUrl'], image_url=recipe['image'], api_id=recipe['id'], vegetarian=recipe['vegetarian'], vegan=recipe['vegan'])
        new_recipe = {"name": recipe['title'], "recipe_url": recipe['sourceUrl'], "image_url": recipe['image'], "api_id": recipe['id'], "vegetarian": recipe['vegetarian'], "vegan": recipe['vegan']}
        recipe_list.append(new_recipe)

    return recipe_list

##############################################################
#Converter

@app.route('/converter')
def show_converter():
    """The converter page"""

    return render_template('converter.html')

##############################################################
#Ratings routes

@app.route('/ratings/rate')
def rating_form():
    """Load form for user to rate/review a recipe"""
    api_id = request.args.get('api_id')

    if not g.user:
        flash("Access unauthorized", 'danger')
        return redirect('/')

    recipe = Recipe.query.filter(Recipe.api_id==api_id).first()
    
    # if the recipe is not already in the DB get info about it from the API and add it to the db
    if recipe == None:
        payload = {'apiKey': API_SECRET_KEY}
        resp = requests.get(f'https://api.spoonacular.com/recipes/{api_id}/information', params=payload)
        recipe_info = resp.json()
        new_recipe = json_to_recipe([recipe_info])
        recipe_add = Recipe.add_recipe(recipe_info[0]['name'], recipe_info[0]['recipe_url'], recipe_info[0]['image_url'], recipe_info['api_id'], recipe_info['vegetarian'], recipe_info['vegan'])
        db.session.commit()
        #left off here
        
    recipe = Recipe.query.filter(Recipe.api_id == api_id).first()
        
    form = RecipeRatingForm()

    return render_template('/rating/rate_recipe.html', form=form, recipe=recipe)


###############################################################
#Home page and error pages

@app.route('/')
def homepage():
    """Show homepage, will need to have validation added"""
    return render_template('home.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/add_recipe', methods=["POST"])
def add_recipe_to_db():
    """Add a recipe to the Recipe table, return recipe id if success of False if not"""
    if not g.user:
        flash("Access unauthorized", 'danger')
        return redirect('/')

    api_id = request.json['recipe_id']
    recipe_url = request.json['recipe_url']
    image_url = request.json['image_url']
    name = request.json['name']
    vegetarian = request.json['vegetarian']
    vegan = request.json['vegan']
    import pdb; pdb.set_trace()

    check_for_recipe = Recipe.query.filter(Recipe.api_id == api_id).first()

    #If the recipe is not already in the recipe table, create a new instance for it
    if not (check_for_recipe):
        new_recipe = Recipe.add_recipe(name, recipe_url, image_url, api_id, vegetarian, vegan)
        db.session.commit()

    return_recipe = Recipe.query.filter(Recipe.api_id==api_id).first()

    if not return_recipe:
        return False 
    else: 
        return {"id": return_recipe.id}
    

