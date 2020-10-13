"""Recipe model tests."""

#to run these tests:
#
#    python -m unittest test_recipe_model.py

from app import app
import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Favorites, Rating, Recipe

#We will connect to a different database for testing before importing the app

os.environ['DATABASE_URL'] = "postgresql:///usemyfood_test"


#Create tables for all tests in one spot
# in each test the data will be deleted

db.create_all()

class RecipeModelTestCase(TestCase):
    """Test model for Recipes."""

    def setUp(self):
        """Create test client and add sample data."""
        db.drop_all()
        db.create_all()

        u1 = User.signup("test_user", "fake@email.com", "password")
        uid1 = 123
        u1.id = uid1

        r1 = Recipe.add_recipe("testtest", "www.test.com", "test.jpg", 56789, True, False)
        rid1 = 1234
        r1.id = rid1 

        db.session.commit()

        self.r1 = r1 
        self.rid1 = rid1 

        self.u1 = u1  
        self.uid1 = uid1

        t_rating = Rating(rating=3.5, user_id=self.uid1, recipe_id=self.rid1, review="It tasted alright, needs more salt")
        db.session.add(t_rating)
        trid = 4589
        t_rating.id = trid
        db.session.commit()

        t_fav = Favorites(user_id=self.uid1, recipe_id=self.rid1)
        tfid = 987
        t_fav.id = tfid
        db.session.add(t_fav)
        db.session.commit()

        self.t_rating = t_rating
        self.trid = trid 

        self.t_fav = t_fav 
        self.tfid = tfid
    
        self.client = app.test_client()
    
    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res 
    
    def test_recipe_model(self):
        """Does the recipe model work?"""

        r = Recipe(
            name="test",
            recipe_url="www.testtest.com",
            image_url="test2.jpg",
            vegetarian=False,
            vegan=False,
            api_id=123456
        )

        db.session.add(r)
        db.session.commit()

        #New recipe should have no ratings or favorites
        self.assertEqual(len(r.ratings), 0)
        self.assertEqual(len(r.favorite), 0)

    ###########################
    # Add Recipe tests
    ###

    def test_valid_add_recipe(self):
        r_test = Recipe.add_recipe("test", "test.com", "test2.jpg", 5555, True, False)
        rtid = 999999
        r_test.id = rtid 
        db.session.commit()

        r_test = Recipe.query.get(rtid)
        self.assertIsNotNone(r_test)
        self.assertEqual(r_test.name, "test")
        self.assertEqual(r_test.recipe_url, "test.com")
        self.assertEqual(r_test.image_url, "test2.jpg")
        self.assertEqual(r_test.api_id, 5555)
        self.assertEqual(r_test.vegetarian, True)
        self.assertEqual(r_test.vegan, False)

    def test_invalid_name(self):
        invalid = Recipe.add_recipe(None, "test.com", "test2.jpg", 5555, True, False)
        rid = 1234567
        invalid.id = rid 
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
    
    def test_invalid_recipe_url(self):
        invalid = Recipe.add_recipe("test", None, "test2.jpg", 5555, True, False)
        rid = 1234567
        invalid.id = rid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
    
    def test_default_image_url(self):
        no_img = Recipe.add_recipe("test","test.com", None, 5555, True, False)
        rid = 1234567
        no_img.id = rid
        db.session.commit()
        test_r = Recipe.query.get(rid)

        self.assertEqual(
            test_r.image_url, "https://www.tastefullysimple.com/_/media/images/recipe-default-image.png")
    
    def test_no_vegetarian(self):
        test_r = Recipe.add_recipe("test", "test.com", "test2.jpg", 5555, None, False)
        rid = 1234567
        test_r.id = rid
        db.session.commit()

        test_r = Recipe.query.get(rid)
        self.assertIsNotNone(test_r)

    def test_no_vegan(self):
        test_r = Recipe.add_recipe(
            "test", "test.com", "test2.jpg", 5555, True, None)
        rid = 1234567
        test_r.id = rid
        db.session.commit()

        test_r = Recipe.query.get(rid)
        self.assertIsNotNone(test_r)
    
    def test_invalid_api_id(self):
        invalid = Recipe.add_recipe("test", "test.com", "test2.jpg", None, True, False)
        rid = 1234567
        invalid.id = rid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
    
    #############################
    # Favorites tests
    ###

    def test_favorite_model(self):
        """Does the favorites model work?"""
        f = Favorites(
            user_id = self.uid1,
            recipe_id = self.rid1
        )
        db.session.add(f)
        db.session.commit()

        self.assertEqual(f.user_id, self.u1.id)
        self.assertEqual(f.recipe_id, self.r1.id)

    def test_invalid_user_id_f(self):
        f = Favorites(
            user_id=None,
            recipe_id=self.rid1
        )
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.add(f)
            db.session.commit()

    def test_invalid_recipe_id_f(self):
        f = Favorites(
            user_id=self.uid1,
            recipe_id=None
        )
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.add(f)
            db.session.commit()

    def test_user_favorites(self):
        """Are the user and favorites models connected"""
        self.assertEqual(len(self.u1.favorites), 1)
        self.assertEqual(self.u1.favorites[0].recipe_id, self.rid1)
        self.assertEqual(self.u1.favorites[0].user_id, self.uid1)
        self.assertEqual(self.u1.favorites[0], self.t_fav)
    
    def test_recipe_favorites(self):
        """Are the recipe and favorites models connected"""
        self.assertEqual(len(self.r1.favorite), 1)
        self.assertEqual(self.r1.favorite[0].user_id, self.uid1)
        self.assertEqual(self.r1.favorite[0].recipe_id, self.rid1)
        self.assertEqual(self.r1.favorite[0].recipe, self.r1)
        self.assertEqual(self.r1.favorite[0], self.t_fav)
    
    
    ###############################
    # Ratings tests
    ###

    def test_ratings_model(self):
        """Does the ratings model work?"""
        r = Rating(
            rating=5,
            user_id=self.uid1,
            recipe_id=self.rid1,
            review="This was great!"
        )
        db.session.add(r)
        db.session.commit()

        self.assertEqual(r.user_id, self.u1.id)
        self.assertEqual(r.recipe_id, self.r1.id)
    
    def test_invalid_rating_r(self):
        r = Rating(rating=None,
                   user_id=self.uid1,
                   recipe_id=self.rid1,
                   review="This was great!"
                   )
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.add(r)
            db.session.commit()
    
    def test_invalid_user_id_r(self):
        r = Rating(rating=3,
                   user_id=None,
                   recipe_id=self.rid1,
                   review="This was great!"
                   )
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.add(r)
            db.session.commit()
    
    def test_invalid_recipe_id_r(self):
        r = Rating(rating=3,
                   user_id=self.uid1,
                   recipe_id=None,
                   review="This was great!"
                   )
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.add(r)
            db.session.commit()
    
    def test_no_review(self):
        r = Rating(rating=3,
                   user_id=self.uid1,
                   recipe_id=self.rid1,
                   review=None
                   )
        db.session.add(r)
        t_id = 123456
        r.id = t_id 
        db.session.commit()

        r = Rating.query.get(t_id)
        self.assertIsNotNone(r)

    def test_user_ratings(self):
        """Are the user and ratings models connected?"""
        self.assertEqual(len(self.u1.ratings), 1)
        self.assertEqual(self.u1.ratings[0].recipe_id, self.rid1)
        self.assertEqual(self.u1.ratings[0].user_id, self.uid1)
        self.assertEqual(self.u1.ratings[0].rating, 3.5)
        self.assertEqual(self.u1.ratings[0].review, "It tasted alright, needs more salt")
    
    def test_recipe_ratings(self):
        """Are the recipe and ratings models connected?"""
        self.assertEqual(len(self.r1.ratings), 1)
        self.assertEqual(self.r1.ratings[0].recipe_id, self.rid1)
        self.assertEqual(self.r1.ratings[0].user_id, self.uid1)
        self.assertEqual(self.r1.ratings[0].rating, 3.5)
        self.assertEqual(
            self.r1.ratings[0].review, "It tasted alright, needs more salt")

    



