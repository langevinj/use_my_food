"""Rating views tests."""

# run tests like"
#
#      FLASK_ENV=production python -m unittest test_rating_views.py

from app import app, CURR_USER_KEY
import os
from unittest import TestCase

from models import db, connect_db, User, Recipe, Favorites, Rating
from bs4 import BeautifulSoup

os.environ['DATABASE_URL'] = "postgresql:///usemyfood_test"


db.create_all()

app.config['WTF_CSRF_ENABLED'] = False

EXAMPLE_FOOD_IMG = "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Perfect_Entrecote_%282454655127%29.jpg/736px-Perfect_Entrecote_%282454655127%29.jpg"


class RatingViewTestCase(TestCase):
    """Test views for ratings."""

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

        self.r1 = Recipe.add_recipe("testrecipe1","www.testrecipe1.com", "testrecipe1.jpg", 1234, True, False)
        self.r2 = Recipe.add_recipe("testrecipe2", "www.testrecipe2.com", "testrecipe2.jpg", 5678, vegetarian=True, vegan=True)
        self.r3 = Recipe.add_recipe("testrecipe3", "www.testrecipe3.com", EXAMPLE_FOOD_IMG, 1357, False, False)
 
        self.r1_id = 468
        self.r1.id = self.r1_id
        self.r2_id = 6810
        self.r2.id = self.r2_id
        self.r3_id = 246
        self.r3.id = self.r3_id
        db.session.commit()

        self.rate1 = Rating(rating=5, user_id=self.u1_id, recipe_id=self.r1_id)
        self.rate2 = Rating(rating=3, user_id=self.u2_id, recipe_id=self.r2_id)
        self.rate3 = Rating(rating=4.5, review="I hated it",
                       user_id=self.testuser_id, recipe_id=self.r1_id)

        db.session.add_all([self.rate1, self.rate2, self.rate3])
        self.rate3_id = 45678
        self.rate3.id = self.rate3_id
        db.session.commit()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

###############################
# Test rating views
###

    def test_user_ratings(self):

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.get(f"/users/{self.testuser_id}/ratings")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("testuser", str(resp.data))
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found_titles = soup.find_all("a", {"class": "title"})
            found_veg = soup.find_all("span", {"class": "vegetarian"})
            found_vegan = soup.find_all("span", {"class": "vegan"})
            found_rating = soup.find_all("small", {"class": "myRating"})
            found_edit_form = soup.find_all("form", {"class": "editRating"})
            found_fav_button = soup.find_all(
                "button", {"class": "favoriteButton"})
            self.assertEqual(len(found_titles), 1)

            #Test for correct "vegetarian" displaying
            self.assertEqual(len(found_veg), 1)

            #Test for correct "vegan" displaying
            self.assertEqual(len(found_vegan), 0)

            #Test for correctly showing a rating
            self.assertIn("My rating:", found_rating[0].text)

            #Test for correct display of "Edit rating" button
            self.assertEqual(len(found_edit_form), 1)

            #Test for correct display of favorite button
            self.assertEqual(len(found_fav_button), 1)

############################
# Rating form view test
###
    
    def test_rating_form(self):

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            recipe = Recipe.query.filter(Recipe.id == self.r2_id).first()
            
            resp = c.get(f'/ratings/rate?api_id={recipe.api_id}')

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Rate testrecipe2", str(resp.data))

    def test_rating_form_new_recipe(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id
            
            #make sure the recipe with api_id of 4 is not in the DB
            recipe = Recipe.query.filter(Recipe.api_id == 4).first()
            self.assertIsNone(recipe)

            resp = c.get('/ratings/rate?api_id=4')

            self.assertEqual(resp.status_code, 200)
            
            #check that the recipe has been added
            recipe = Recipe.query.filter(Recipe.api_id == 4).first()
            self.assertIsNotNone(recipe)
            self.assertIn(f"Rate {recipe.name}", str(resp.data))
    
    def test_unauthorized_rating_form(self):
        with self.client as c:

            #make sure the recipe with api_id of 4 is not in the DB
            recipe = Recipe.query.filter(Recipe.api_id == 4).first()
            self.assertIsNone(recipe)

            resp = c.get('/ratings/rate?api_id=4', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            #recipe should no have been added to the db
            recipe = Recipe.query.filter(Recipe.api_id == 4).first()
            self.assertIsNone(recipe)

#########################
# Add rating tests
###

    def test_add_rating(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            ratings = Rating.query.all()
            self.assertEqual(len(ratings), 3)
            
            resp = c.post('/ratings/add_rating', content_type='multipart/form-data', data={"rating": 1.5, "review": "testreview", "recipe_id": self.r2_id}, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Review added", str(resp.data))

            #the rating should have been added to the DB
            ratings = Rating.query.all()
            self.assertEqual(len(ratings), 4)
    
    def test_unauthorized_add_rating(self):
        with self.client as c:
            ratings = Rating.query.all()
            self.assertEqual(len(ratings), 3)

            resp = c.post('/ratings/add_rating', content_type='multipart/form-data', data={
                          "rating": 1.5, "review": "testreview", "recipe_id": self.r2_id}, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            #the rating should NOT have been added to the DB
            ratings = Rating.query.all()
            self.assertEqual(len(ratings), 3)

##########################
# Edit rating tests
###

    def test_edit_rating_form(self):

        with self.client as c:
            resp = c.get(f'/ratings/edit?rating_id=45678')

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Edit rating for", str(resp.data))
    
    def test_edit_rating(self):

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            check_rating = Rating.query.get(45678)

            self.assertEqual("I hated it", check_rating.review)

            resp = c.post('/ratings/edit', content_type='multipart/form-data', data={
                          'review': 'It was good', 'rating': 3.5, 'user_id': self.testuser_id, 'rating_id': 45678}, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            #Check that the review has changed
            check_rating = Rating.query.get(45678)
            self.assertIsNot("I hated it", check_rating.review)
            self.assertEqual(3.5, check_rating.rating)
    
    def test_unauthenticated_edit_rating(self):

        with self.client as c:
            check_rating = Rating.query.get(45678)

            resp = c.post('/ratings/edit', content_type='multipart/form-data', data={
                          'review': 'It was good', 'rating': 3.5, 'user_id': self.testuser_id, 'rating_id': 45678}, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))
            rating_after = Rating.query.get(45678)

            #rating should not have been changed
            self.assertEqual(check_rating.review, rating_after.review)

############################
    
    def test_unauthorized_ratings_page_access(self):

        with self.client as c:
            resp = c.get(f"/users/{self.testuser_id}/ratings", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("testuser's Ratings:", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))
    
    def test_get_all_rated_recipes(self):
        """Should return a list of all api_ids for recipes that have been rated"""
        with self.client as c:
            resp = c.get('/ratings/all_recipe_ids')

            self.assertEqual(resp.status_code, 200)

    def test_show_recipe_ratings(self):

        with self.client as c:
            resp = c.get(f'/ratings?api_id={self.r1.api_id}')

            self.assertEqual(resp.status_code, 200)

            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found_ratings = soup.find_all("li", {"class": "rating"})

            self.assertEqual(len(found_ratings), 2)

