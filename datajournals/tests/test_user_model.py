from unittest import TestCase

from datajournals.models.authorization import User


class UserModelTestCase(TestCase):
    def test_password_setter(self):
        user = User()
        user.password = 'cat'
        self.assertTrue(user.password_hash is not None)

    def test_no_password_getter(self):
        user = User()
        user.password = 'cat'
        with self.assertRaises(AttributeError):
            user.password

    def test_password_verification(self):
        user = User()
        user.password = 'cat'
        self.assertTrue(user.verify_password('cat'))
        self.assertFalse(user.verify_password('dog'))

    def test_password_salts_are_random(self):
        user1 = User()
        user1.password = 'cat'
        user2 = User()
        user2.password = 'cat'
        self.assertTrue(user1.password_hash != user2.password_hash)
