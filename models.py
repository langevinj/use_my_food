"""SQLAlchemy models for Use My Food"""

from flask_bcrypt import Bcrypt 
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()

def connect_db(app):
    """Connect this database to the Flask app"""

    db.app = app
    db.init_app(app)

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
        unqiue=True,
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
        'Recipe',
        secondary="favorites"
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
            db.ForeignKey('recipes.id', ondelete='cascade')
        )