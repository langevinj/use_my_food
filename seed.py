from app import db   
from models import User, Recipe, Favorites

db.drop_all()
db.create_all()

user1 = User.signup(username="testtest", email="test@gmail.com", password="123456")

user2 = User.signup(username="testtest2", email="test2@gmail.com", password="123456")

user3 = User.signup(username="testtest3", email="test3@gmail.com", password="123456")

db.session.commit()

recipe1 = Recipe(name="Pork Lo mein",
                 recipe_url="https://www.allrecipes.com/recipe/231523/pork-lo-mein/")
recipe2 = Recipe(name="Spagetti and Meatballs",
                 recipe_url="https://www.delish.com/cooking/recipe-ideas/recipes/a55764/best-spaghetti-and-meatballs-recipe/")
recipe3 = Recipe(name="Pineapple Chicken",
                 recipe_url="https://www.dinneratthezoo.com/pineapple-chicken/")

db.session.add_all([recipe1, recipe2, recipe3])
db.session.commit()

fav1 = Favorites(user_id=1, recipe_id=2)

db.session.add(fav1)
db.session.commit()
