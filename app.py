import os 

from flask import Flask, render_template, request, flash, redirect, session, g, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from secret import API_SECRET_KEY
from models import db, connect_db, User, Favorites, Recipe, toggle_favorites
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
    """Return a list of the current user's favorites' recipe ids"""
    favIds = []
    favorites = g.user.favorites

    for favorite in favorites:
        favIds.append(favorite.recipe_id)
    
    return {"favIds":favIds}

@app.route('/users/toggle_favorite/', methods=["POST"])
def add_favorite():
    """Toggle a user's favorite, respond to JS with favorited or unfavorited"""
    if not g.user:
        flash("Access unauthorized", 'danger')
    recipe_id = request.json['recipe_id']
    img_src = request.json['img_src']
    name = request.json['name']
    recipe_url = request.json['recipe_url']

    response = toggle_favorites(int(recipe_id), g.user.id, str(img_src), name, recipe_url)
    
    return response

##############################################################
#Searching by recipe

@app.route('/search', methods=["POST"])
def search_by_recipe():
    """Save searched recipes and return a serialized list"""
    data = request.json['data']
    results_list = data['data']['results']
    searched_recipes = []

    for recipe in results_list:
        new_recipe = Recipe.add_recipe(recipe['title'], recipe['sourceUrl'], recipe['image'], recipe['id'], recipe['vegetarian'], recipe['vegan'])
        db.session.commit()
        get_recipe = Recipe.query.get(new_recipe.id)
        serialized_recipe = serialize_recipe(get_recipe)
        searched_recipes.append(serialized_recipe)
    
    search_term = request.json['search_term']
    res = {"search_term": search_term, "searched_recipes": searched_recipes}
    return res

@app.route('/search/<search_term>')
def redirect_to_search(search_term):

    return redirect(f'/search_results/{search_term}')

# @app.route('/search_results', methods=["POST"])
# def display_search_results():
#     """display the recipes returned from the search"""
#     data = request.json['data']
#     search_term = data["search_term"]
#     searched_recipes = data["searched_recipes"]
#     import pdb; pdb.set_trace()

#     return render_template('search/search_results.html', searched_recipes=searched_recipes, search_term=search_term)

@app.route('/search_results/<search_term>')
def earch_results_page(search_term):

    return render_template('/search/searchresults.html', search_term=search_term)

###############################################################
#Home page and error pages

@app.route('/')
def homepage():
    """Show homepage, will need to have validation added"""
    return render_template('home.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


def serialize_recipe(recipe):
    """Serialize a recipe SQLAlchemy element to dictionary"""

    return {
        "id": recipe.id,
        "name": recipe.name,
        "recipe_url": recipe.recipe_url,
        "image_url": recipe.image_url,
        "vegetarian": recipe.vegetarian,
        "vegan": recipe.vegan,
        "api_id": recipe.api_id,
    }
