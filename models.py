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

# class Rating(db.Model):
#     """Recipe rating class"""

#     __tablename__ = "rating"

#     id = db.Column(
#         db.Integer,
#         primary_key=True
#     )

#     rating = db.Column(
#         db.Integer,
#         nullable=False
#     )

#     user_id = db.Column(
#         db.Integer,
#         db.ForeignKey('users.id', ondelete='cascade')
#     )

#     recipe_id = db.Column(
#         db.Integer,
#         db.ForeignKey('recipes.id', ondelete='cascade')
#     )


class Favorites(db.Model):
    """Favorites class"""

    __tablename__ = "favorites"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='cascade')
    )

    recipe_id = db.Column(
        db.Integer, 
        nullable=False
    )


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

    # ratings = db.relationship(
    #     "User",
    #     secondary="rating",
    #     primaryjoin=(Rating.user_id == id),
    #     secondaryjoin=(Rating.recipe_id == Recipe.id)
    # )


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
    
# class Recipe(db.Model):
#     """Recipe class"""

#     __tablename__ = "recipes"

#     id = db.Column(
#         db.Integer,
#         primary_key=True
#     )

#     name = db.Column(
#         db.Text,
#         nullable=False
#     )

#     recipe_url = db.Column(
#         db.String,
#         nullable=False
#     )

#     image_url = db.Column(
#         db.String,
#         nullable=False,
#         default=DEFAULT_IMG_URL
#     )

    # favorited_by = db.relationship(
    #     'User',
    #     secondary='favorites'
    # )

    # ratings = db.relationship(
    #     "Recipe",
    #     secondary="rating",
    #     primaryjoin=(Rating.recipe_id == id),
    #     secondaryjoin=(Rating.user_id == User.id)
    # )


###########
#Helper methods

def toggle_favorites(recipe_id, user_id):
    """Toggle a favorite for a user on or off by adding or deleting it to the favorite table"""
    all_favorites = user_favorites_list(user_id)
    all_favorites_id = []
    
    for fav in all_favorites:
        all_favorites_id.append(fav.recipe_id)
    
    if recipe_id in all_favorites_id:
        recipe = Favorites.query.filter(Favorites.recipe_id==recipe_id).first()
        db.session.delete(recipe)
        db.session.commit()
        return "unfavorited"
    else:
        newFav = Favorites(user_id=user_id, recipe_id=recipe_id)
        db.session.add(newFav)
        db.session.commit()
        return "favorited"

def user_favorites_list(user_id):
    """Create a list of all the user's favorites"""

    user = User.query.get(user_id)
    return user.favorites
