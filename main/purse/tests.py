"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase, Client
from django.test.client import Client as Client2


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)

class LoginTest(TestCase):
    def test_loginfind(self):
        response = self.client.get('/accounts/login/')
        self.failUnlessEqual(response.status_code, 200)

    def test_logout(self):
        response = self.client.get('/accounts/logout/')
        self.failUnlessEqual(response.status_code, 200)
    
    def test_nologin(self):
        response = self.client.get('/invoice/view/')
        self.failUnlessEqual(response.status_code, 302)

    def test_login(self):
        # First check for the default behavior
        response = self.client.get('/')
        self.assertRedirects(response, '/accounts/login/?next=/')

    def test_auth(self):
        response = self.client.post('/accounts/login/', {'username': 'john', 'password': 'smith'})
        self.failUnlessEqual(response.status_code, 200)
