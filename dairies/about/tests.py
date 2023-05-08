from http import HTTPStatus

from django.test import Client, TestCase


class AboutTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()

    def test_author_url_at_desired_location(self):
        response = AboutTests.guest_client.get('/dairies/about/author/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_view_uses_correct_template(self):
        response = AboutTests.guest_client.get('/dairies/about/author/')
        template = 'about/author.html'
        self.assertTemplateUsed(response, template)
