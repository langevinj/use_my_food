"""User model tests."""

#to run these tests:
#
#    python -m unittest test_user_model.py

import os
from unittest import TestCase
from sqlalchemy import exc 

from models import db, User, Favorites, Rating, Recipe

#We will connect to a different database for testing before importing the app

os.environ['DATABASE_URL'] = "postgresql:///usemyfood_test"

from app import app

#Create tables for all tests in one spot
# in each test the data will be deleted

db.create_all()

class UserModelTestCase(TestCase):
    """Test model for Users."""

    def setUp(self):
        """Create test client and add sample data."""
        db.drop_all()
        db.create_all()

        u1 = User.signup("test1", "fake@email.com", "password")
        uid1 = 123
        u1.id = uid1

        u2 = User.signup("test2", "fake2@email.com", "password")
        uid2 = 321
        u2.id = uid2 

        r1 = Recipe(name="Test", recipe_url="testrecipe.com", image_url="testimage.jpg", vegetarian=True, vegan=False, api_id=123456789)
        rid = 4567
        r1.id = rid 
        db.session.add(r1)
        
        db.session.commit()

        u1 = User.query.get(uid1)
        u2 = User.query.get(uid2)
        r1 = Recipe.query.get(rid)

        self.u1 = u1 
        self.uid1 = uid1

        self.u2 = u2 
        self.uid2 = uid2

        self.r1 = r1 
        self.rid1 = rid

        self.client = app.test_client()
    
    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res 

    def test_user_model(self):
        """Does the model work?"""

        u = User(
            username="testuser",
            email="test@test.com",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        #New user should have no ratings or favorites
        self.assertEqual(len(u.favorites), 0)
        self.assertEqual(len(u.ratings), 0)


    ##################################################

    def test_user__repr__(self):
        """Does __repr__ method work?"""
        self.assertEqual(f"{self.u1}", f"<User #{self.u1.id}: {self.u1.username}, {self.u1.email}>")


    #######################
    # Authentication Testing
    ###

    def test_valid_authentication(self):
        u = User.authenticate(self.u1.username, "password")
        self.assertIsNotNone(u)
        self.assertEqual(u.id, self.uid1)
    
    def test_invalid_username(self):
        self.assertFalse(User.authenticate("wrongusername", "password"))
    
    def test_wrong_password(self):
        self.assertFalse(User.authenticate(self.u1.username, "wrongpassword"))


    #######################
    # Signup Tests
    ###

    def test_valid_signup(self):
        u_test = User.signup("testtest", "testtest@test.com", "password")
        uid = 99999
        u_test.id = uid 
        db.session.commit()

        u_test = User.query.get(uid)
        self.assertEqual(u_test.username, "testtest")
        self.assertEqual(u_test.email, "testtest@test.com")
        self.assertNotEqual(u_test.password, "password")
        #Because Bcrypt was used, password strings should start with $2b$
        self.assertTrue(u_test.password.startswith('$2b$'))

    def test_invalid_username(self):
        invalid = User.signup(None, "test@test.com", "password")
        uid = 1234567
        invalid.id = uid 
        with self.assertRaises(exc.IntegrityError) as content:
            db.session.commit()
    
    def test_invalid_email(self):
        invalid = User.signup("test3", None, "password")
        uid = 1235689
        invalid.id = uid 
        with self.assertRaises(exc.IntegrityError) as content:
            db.session.commit()
    
    def test_invalid_password(self):
        with self.assertRaises(ValueError) as content:
            User.signup("testtest", "email@email.com", None)
    

    ##########################
    #Favorites test
    ###
    
    # def test_user_favorites(self):
    #     test_fav = Favorites(user_id=self.uid1, recipe_id=self.rid1)
    #     testid = 896745
    #     test_fav.id = testid
    #     db.session.commit()

    #     self.assertEqual(len(self.u1.favorites), 1)
    #     self.assertEqual(len(self.u2.favorites), 0)

    #     self.assertEqual(self.u1.favorites[0].id, 896745)
    #     self.assertEqual(self.u1.favorites[0].recipe_id, self.rid1)
    #     self.assertEqual(self.u1.favorites[0].user_id, self.uid1)
    

    # ##########################
    # #Ratings test
    # ###

    # def test_user_ratings(self):
    #     test_rate = Rating(rating=3.5, user_id=self.uid1, recipe_id=self.rid1, review="It tasted alright, needs more salt")
    #     testid = 9876543
    #     test_rate.id = testid 
    #     db.session.commit()

    #     self.assertEqual(len(self.u1.ratings), 1)
    #     self.assertEqual(len(self.u2.ratings), 0)

    #     self.assertEqual(self.u1.ratings[0].recipe_id, self.rid1)
    #     self.assertEqual(self.u1.ratings[0].rating, 3.5)
    #     self.assertEqual(self.u1.ratings[0].review, "It tasted alright, needs more salt")
    #     self.assertEqual(self.u1.ratings[0].id, test_rate.id)

