from unittest import TestCase

from flask import current_app

from datajournals import create_app, db


class BasicsTestCase(TestCase):

    def setup(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_app_exists(self):
        self.assertFalse(current_app is None)

    def test_app_is_testing(self):
        self.assertTrue(current_app.config['TESTING'])
