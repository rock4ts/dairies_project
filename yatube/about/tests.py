from http import HTTPStatus

from django.test import Client, TestCase


class AboutTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_author_url_at_desired_location(self):
        response = self.guest_client.get('/about/author/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_tech_url_at_desired_location(self):
        response = self.guest_client.get('/about/tech/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_view_uses_correct_template(self):
        response = self.guest_client.get('/about/author/')
        template = 'about/author.html'
        self.assertTemplateUsed(response, template)
