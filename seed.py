from app import db   
from models import User, Recipe, Favorites

db.drop_all()
db.create_all()

