"""User views tests."""

# run tests like"
#
#      FLASK_ENV=production python -m unittest test_user_views.py

import os
from unittest import TestCase

from models import db, connect_db, User, Recipe, Favorites, Rating
from bs4 import BeautifulSoup

os.environ['DATABASE_URL'] = "postgresql:///usemyfood_test"

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False

EXAMPLE_FOOD_IMG = "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Perfect_Entrecote_%282454655127%29.jpg/736px-Perfect_Entrecote_%282454655127%29.jpg"

class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser")
        
        self.testuser_id = 9999
        self.testuser.id = self.testuser_id

        self.u1 = User.signup("abc", "test1@test.com", "password")
        self.u1_id = 789
        self.u1.id = self.u1_id
        self.u2 = User.signup("efg", "test2@test.com", "password")
        self.u2_id = 678
        self.u2.id = self.u2_id
        self.u3 = User.signup("hij", "test3@test.com", "password")
        self.u3_id = 4567
        self.u3.id = self.u3_id

        db.session.commit()
    
    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp 
    
    ##########################
    
    def test_users_delete_page(self):
        with self.client as c:
            resp = c.get('/users/789')

            self.assertIn("abc", str(resp.data))
            self.assertIn("delete", str(resp.data))
    
    ###########################
    # Setup functions
    ###
    
    def setup_recipes(self):
        r1 = Recipe(name="testrecipe1", recipe_url="www.testrecipe1.com",
                    image_url="testrecipe1.jpg", vegetarian=True, vegan=False, api_id=1234)
        r2 = Recipe(name="testrecipe2", recipe_url="www.testrecipe2.com",
                    image_url="testrecipe2.jpg", vegetarian=True, vegan=True, api_id=5678)
        r3 = Recipe(name="testrecipe3", recipe_url="www.testrecipe3.com",
                    image_url=EXAMPLE_FOOD_IMG, vegetarian=False, vegan=False, api_id=1357)
        db.session.add_all([r1, r2, r3])
        r1_id = 468
        r1.id = r1_id
        r2_id = 6810
        r2.id = r2_id
        r3_id = 246
        r3.id = r3_id
        db.session.commit()

    def setup_favorites(self):
        f1 = Favorites(user_id=self.testuser_id, recipe_id=468)

        db.session.add(f1)
        db.session.commit()
    
    ##########################
    # Test favorite views
    ###
    
    def test_user_show_favorites(self):
        self.setup_recipes()
        self.setup_favorites()
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.get(f"/users/{self.testuser_id}/favorites")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("testuser", str(resp.data))
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found_titles = soup.find_all("a", {"class": "title"})
            found_veg = soup.find_all("span", {"class": "vegetarian"})
            found_vegan = soup.find_all("span", {"class": "vegan"})
            found_rate_button = soup.find_all("form", {"class": "rateButton"})

            # Test for correct amount of favorites
            self.assertEqual(len(found_titles), 1)

            # Test for correct Vegetarian labelling
            self.assertEqual(len(found_veg), 1)

            #Test for correct Vegan labelling
            self.assertEqual(len(found_vegan), 0)

            #Test correctly displaying "Rate this Recipe" button
            self.assertEqual(len(found_rate_button), 1)

            # Test for the correct title in the favorite link
            self.assertIn("testrecipe1", found_titles[0].text)
    
    def test_add_favorite(self):
        r4 = Recipe(name="testrecipe4", recipe_url="www.testrecipe4.com", image_url=EXAMPLE_FOOD_IMG, vegetarian=False, vegan=False, api_id=1212)
        db.session.add(r4)
        r4_id = 98765
        r4.id = 98765
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id
            
            resp = c.post('/users/toggle_favorite', json={"id": 98765}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            favorites = Favorites.query.filter(Favorites.recipe_id==98765).all()
            self.assertEqual(len(favorites), 1)
            self.assertEqual(favorites[0].user_id, self.testuser_id)
    
    def test_remove_favorites(self):
        self.setup_recipes()
        self.setup_favorites()

        r = Recipe.query.filter(Recipe.name=="testrecipe1").one()
        self.assertIsNotNone(r)

        f = Favorites.query.filter(Favorites.user_id==self.testuser_id and Favorites.recipe_id==r.id).one()

        #Make sure the test user has favorited the recipe:
        self.assertIsNotNone(f)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id
            
            resp = c.post('/users/toggle_favorite',
                          json={"id": r.id}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            favorites = Favorites.query.filter(Favorites.recipe_id==r.id).all()

            #the favorite has been removed
            self.assertEqual(len(favorites), 0)

    def test_unauthenticated_favorite(self):
        self.setup_recipes()
        self.setup_favorites()

        r = Recipe.query.filter(Recipe.name=="testrecipe1").one()
        self.assertIsNotNone(r)

        favorite_count = Favorites.query.count()

        with self.client as c:
            resp = c.post('/users/toggle_favorite', json={"id": r.id}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIn("Access unauthorized", str(resp.data))

            # The number of favorites hasn't changed since making the request
            self.assertEqual(favorite_count, Favorites.query.count())
    
    def test_unauthorized_favorites_page_access(self):
        self.setup_recipes()
        self.setup_favorites()

        with self.client as c:
            resp = c.get(f'/users/{self.testuser_id}/favorites', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
    

    ########################
    # Search testing
    ###

    def test_search_by_recipe(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.post('/search', content_type='multipart/form-data', data={"searchRecipeTerm": "kale"})

            self.assertEqual(resp.status_code, 200)

            self.assertIn("Search: kale", str(resp.data))
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found_recipes = soup.find_all("a", {"class": "title"})

            self.assertEqual(len(found_recipes), 5)

    def test_invalid_term_search_by_recipe(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.post('/search', content_type='multipart/form-data',
                          data={"searchRecipeTerm": "mshfgaskdfgnasugfa"}, follow_redirects=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("No recipes with this name have been found", str(resp.data))
    
    ##########################
    # Converter testing
    ###

    def test_show_converter(self):
        with self.client as c:
            
            resp = c.get('/converter')

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Convert From:", str(resp.data))
    








    
    
