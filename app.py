import os 
import requests
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, flash, redirect, session, g, jsonify
from flask_debugtoolbar import DebugToolbarExtension
# from secret import API_SECRET_KEY, TEST_API_SECRET_KEY
from models import db, connect_db, User, Favorites, Recipe, toggle_favorites, Rating
from sqlalchemy.exc import IntegrityError
from forms import UserAddForm, LoginForm

#remove this eventually
CURR_USER_KEY = "curr_user"

BASE_URL = "http://127.0.0.1:5000"
SEARCH_BY_ING_URL = "https://api.spoonacular.com/recipes/findByIngredients"

app = Flask(__name__)
#Get DB_URI from environ variable or, if not set there, user development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', "postgres:///usemyfood_db")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
app.config['API_SECRET_KEY'] = os.environ.get('API_SECRET_KEY')
API_SECRET_KEY = os.environ.get('API_SECRET_KEY')
toolbar = DebugToolbarExtension(app)

connect_db(app)


########################
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
            if "users_email_key" in str(e) and "users_username_key" in str(e):
                flash("Username and email already used", 'danger')
                return render_template('users/signup.html', form=form)
            elif "users_email_key" in str(e):
                flash("Already an account associated with this email", 'danger')
                return render_template('users/signup.html', form=form)
            elif "users_username_key" in str(e):
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
# User routes:

@app.route('/users/<int:user_id>')
def user_delete(user_id):
    """Show a users a prompt to delete their account"""

    user = User.query.get_or_404(user_id)
    return render_template("users/delete.html", user=user)


@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete a user's account"""
    if not g.user:
        flash("Access unauthorized", 'danger')
        return redirect('/login')

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect('/signup')


@app.route('/users/<int:user_id>/favorites')
def user_favorites(user_id):
    """Display a list of the users favorites"""

    if not g.user:
        flash("Access unauthorized", 'danger')
        return redirect('/signup')

    user = User.query.get_or_404(user_id)

    favorites = user.favorites
    has_ratings = []

    for fav in favorites:
        rating = Rating.query.filter(Rating.recipe_id == fav.recipe_id).all()
        if len(rating) != 0:
            has_ratings.append(fav.id)

    return render_template('users/favorites.html', user=user, favorites=favorites, has_ratings=has_ratings)

@app.route('/users/<int:user_id>/ratings')
def user_ratings(user_id):
    """Display a list of ratings the user has provided"""
    if not g.user:
        flash("Access unauthorized", 'danger')
        return redirect('/login')

    user = User.query.get_or_404(user_id)

    ratings = user.ratings
    recipes = []

    for rating in ratings:
        recipe = Recipe.query.get(rating.recipe_id)
        recipes.append(recipe)

    return render_template('users/ratings.html', user=user, ratings=ratings, recipes=recipes)

########################################################

@app.route('/ratings/edit', methods=["GET"])
def edit_rating_form():
    """Allow a user to edit a rating"""
    rating_id = request.args.get('rating_id')
    rating = Rating.query.get_or_404(rating_id)

    return render_template('rating/edit.html', rating=rating)

@app.route('/ratings/edit', methods=["POST"])
def edit_rating():
    """Rewrite previos rating by a user"""
    if not g.user:
        flash("Access unauthorized", 'danger')
        return redirect('/login')
    
    review = request.form['review']
    rating = request.form['rating']
    user_id = request.form['user_id']
    rating_id = request.form['rating_id']

    rating_to_edit = Rating.query.get_or_404(rating_id)

    rating_to_edit.review = review 
    rating_to_edit.rating = rating 

    db.session.commit()

    flash("Review updated", "success")
    return redirect(f'/users/{user_id}/ratings')



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
        return redirect('/login')
    
    id = request.json['id']
    response = toggle_favorites(id, g.user.id)
    
    return response

##############################################################
#Searching by recipe
@app.route('/search', methods=["POST"])
def search_by_recipe():
    """Request recipe information based on the title of the searched recipe"""
    user = User.query.get(g.user.id)

    search_term = request.form['searchRecipeTerm']

    #change the number here to change the amount of recipes returned, then search for recipes by recipe name
    payload = {'query': search_term, 'number': 5, 'addRecipeInformation': 'true', 'apiKey': API_SECRET_KEY}
    resp = requests.get('https://api.spoonacular.com/recipes/complexSearch', params=payload)

    search_results = resp.json()['results']

    #if no results are found, or if therefore the query is not valid, respond with an error
    if len(search_results) == 0:
        flash("No recipes with this name have been found", 'danger')
        return redirect('/login')

    #clean up all the information not needed by the page
    recipe_list = json_to_recipe(search_results)

    #idicate whether there are ratings for each result
    has_ratings = []

    for recipe in recipe_list:
        rating = Recipe.query.filter(
            Recipe.api_id == recipe['api_id'] and Recipe.ratings != 0).all()
        if len(rating) != 0:
            has_ratings.append(recipe['api_id'])

    return render_template('search/searchresults.html', search_term=search_term, recipe_list=recipe_list, has_ratings=has_ratings, user=user)


def json_to_recipe(recipes):
    """Clean up a list of json recipes into a simpler recipe list of objects"""
    recipe_list = []
    for recipe in recipes:
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
        return redirect('/login')

    recipe = Recipe.query.filter(Recipe.api_id==api_id).first()
    
    # if the recipe is not already in the DB get info about it from the API and add it to the db
    if recipe == None:
        payload = {'apiKey': API_SECRET_KEY}
        resp = requests.get(f'https://api.spoonacular.com/recipes/{api_id}/information', params=payload)
        recipe_info = resp.json()
        new_recipe = json_to_recipe([recipe_info])[0]
        recipe_add = Recipe.add_recipe(new_recipe['name'], new_recipe['recipe_url'], new_recipe['image_url'], new_recipe['api_id'], new_recipe['vegetarian'], new_recipe['vegan'])
        db.session.commit()
        
    recipe = Recipe.query.filter(Recipe.api_id == api_id).first()

    return render_template('/rating/rate_recipe.html', recipe=recipe)

@app.route('/ratings/add_rating', methods=["POST"])
def add_rating():
    """Add a rating the to rating DB"""
    if not g.user:
        flash("Access unauthorized", 'danger')
        return redirect('/login')

    resp = request.form

    rating = float(resp.get("rating"))
    review = resp.get("review")
    id = int(resp.get('recipe_id'))

    new_rating = Rating(rating=rating, user_id=g.user.id, recipe_id=id, review=review)
    db.session.add(new_rating)
    db.session.commit()

    flash("Review added", 'success')
    return redirect("/")

@app.route('/ratings/all_recipe_ids')
def get_all_rated_recipes():
    """Return a list of all api_id's for recipes that have been rated"""
    rated_recipes = Recipe.query.filter(Recipe.ratings != None).all()

    ids = []
    for recipe in rated_recipes:
        ids.append(recipe.api_id)

    return {"ids": ids}

@app.route('/ratings')
def show_recipe_ratings():
    """Show all ratings for a specified recipe"""
    api_id = request.args['api_id']

    recipe = Recipe.query.filter(Recipe.api_id == api_id).first()

    if not recipe:
        flash("No recipes with this id", 'danger')
        return redirect('/')

    return render_template('/rating/ratings.html', recipe=recipe)


###############################################################
#Home page and error pages

@app.route('/')
def homepage():
    """Show homepage, will need to have validation added"""
    if not g.user:
        return redirect('/signup')

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

######################################################################
# Helper requests from JS
###

@app.route('/ingredient-search', methods=["POST"])
def search_by_ingredient():
    """Help json by returning entire recipe search by ingredient"""

    numRecipes = request.json['number']
    ingStr = request.json['ingStr']
    payload = {'ingredients': ingStr, 'number': numRecipes, 'apiKey': API_SECRET_KEY}
    resp = requests.get(f'{SEARCH_BY_ING_URL}', params=payload)
    data = resp.json()
    json_response = {"data": data}
    return json_response


# @app.route('/ingredient-search-1-recipe', methods=["POST"])
# def search_by_ingredient_1_recipe():

@app.route('/ingredient-search-recipes-helper', methods=["POST"])
def search_by_ingredient_recipe_helper():
    """Get recipe information from API and return it to app.js"""
    ids = request.json['ids']
    payload = {'ids': ids, 'apiKey': API_SECRET_KEY}
    resp = requests.get(f'https://api.spoonacular.com/recipes/informationBulk', params=payload)
    data = resp.json()
    json_response = {"data": data}
    return json_response

@app.route('/converter-helper', methods=["POST"])
def convert_helper():
    """Help JS converter request, send request to API"""
    sourceIngredient = request.json['sourceIngredient']
    sourceAmount = request.json['sourceAmount']
    sourceUnit = request.json['sourceUnit']
    targetUnit = request.json['targetUnit']

    payload = {"ingredientName": sourceIngredient, "sourceAmount": sourceAmount, "sourceUnit": sourceUnit, "targetUnit": targetUnit, "apiKey": API_SECRET_KEY}
    resp = requests.get(f'https://api.spoonacular.com/recipes/convert', params=payload)
    data = resp.json()
    json_response = {"data": data}
    return json_response


