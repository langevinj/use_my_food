"""SQLAlchemy models for Use My Food"""

from flask_bcrypt import Bcrypt 
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()

def connect_db(app):
    """Connect this database to the Flask app"""

    db.app = app
    db.init_app(app)

DEFAULT_IMG_URL = "https://www.tastefullysimple.com/_/media/images/recipe-default-image.png"

class Rating(db.Model):
    """Recipe rating class"""

    __tablename__ = "ratings"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    rating = db.Column(
        db.Float,
        nullable=False,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='cascade'),
        nullable=False
    )

    recipe_id = db.Column(
        db.Integer,
        db.ForeignKey('recipes.id', ondelete='cascade'),
        nullable=False
    )

    review = db.Column(
        db.Text,
        nullable=True,
    )

    recipe= db.relationship("Recipe")


class Favorites(db.Model):
    """Favorites class"""

    __tablename__ = "favorites"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='cascade'),
        nullable=False
    )

    recipe_id = db.Column(
        db.Integer,
        db.ForeignKey('recipes.id', ondelete="cascade"),
        nullable=False
    )

    recipe = db.relationship("Recipe")


class User(db.Model):
    """User in system"""

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    username = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True
    )

    password = db.Column(
        db.Text,
        nullable=False,
    )

    favorites = db.relationship(
        "Favorites"
    )

    ratings = db.relationship(
        "Rating", backref="users"
    )


    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"
    
    @classmethod 
    def signup(cls, username, email, password):
        """Sign up a user.

        Hashes password and adds user to system
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
        )

        db.session.add(user)
        return user
    
    @classmethod
    def authenticate(cls, username, password):
        """Find user with 'username' and 'password'.

        Returns user object if the user exist, otherwise, or if password is wrong
        returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user 
        
        return False
    
class Recipe(db.Model):
    """Recipe class"""

    __tablename__ = "recipes"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.Text,
        nullable=False
    )

    recipe_url = db.Column(
        db.String,
        nullable=False
    )

    image_url = db.Column(
        db.String,
        nullable=False,
        default=DEFAULT_IMG_URL
    )

    vegetarian = db.Column(
        db.Boolean,
        nullable=True
    )

    vegan = db.Column(
        db.Boolean,
        nullable=True
    )

    api_id = db.Column(
        db.Integer,
        nullable=False,
        unique=True,
    )

    favorite = db.relationship(
        "Favorites"
    )

    ratings = db.relationship(
        "Rating"
    )

    @classmethod
    def add_recipe(cls, name, recipe_url, image_url, api_id, vegetarian=False, vegan=False):
        """ Adds a recipe to the recipe table """

        recipe = Recipe(
            name=name,
            recipe_url=recipe_url,
            image_url=image_url,
            vegetarian=vegetarian,
            vegan=vegan,
            api_id=api_id,
        )

        db.session.add(recipe)
        return recipe


###########
#Helper methods

def toggle_favorites(recipe_id, user_id):
    """Toggle a favorite for a user on or off by adding or deleting it to the favorite table"""
    all_favorites = user_favorites_list(user_id)
    all_favorites_id = []
    
    for fav in all_favorites:
        if fav.recipe_id == recipe_id:
            db.session.delete(fav)
            db.session.commit()
            print("unfavorited")
            return "unfavorited"
    
    newFav = Favorites(user_id=user_id, recipe_id=recipe_id)
    db.session.add(newFav)
    db.session.commit()
    print("favorited")
    return "favorited"


def user_favorites_list(user_id):
    """Create a list of all the user's favorites"""

    user = User.query.get(user_id)
    return user.favorites
