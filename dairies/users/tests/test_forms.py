from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class TestUsersForms(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_signup_creates_user(self):
        users_count = User.objects.count()
        form_data = {
            'username': 'rock4ts',
            'password1': 'test!password',
            'password2': 'test!password',
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertEqual(User.objects.count(), users_count + 1)
        self.assertTrue(
            User.objects.filter(username='rock4ts').exists()
        )
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
