from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_author = User.objects.create_user(username='rock4ts')
        cls.test_nonauthor = User.objects.create_user(username='someone')
        cls.test_group = Group.objects.create(
            title='Тестовое сообщество',
            slug='test-slug',
            description='Тестовое описание сообщества',
        )
        cls.test_post = Post.objects.create(
            text='Тестовый текст',
            author=cls.test_author,
            group=cls.test_group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.nonauthor = PostsURLTests.test_nonauthor
        self.authorized_client.force_login(self.nonauthor)
        self.author_client = Client()
        self.author = PostsURLTests.test_author
        self.author_client.force_login(self.author)

    def test_no_login_urls_at_desired_location(self):
        test_slug = PostsURLTests.test_group.slug
        test_post_id = PostsURLTests.test_post.id
        test_username = PostsURLTests.test_author.username
        url_response_dict = {
            '/':
            self.client.get('/'),
            '/group/<slug:slug>/':
            self.client.get(f'/group/{test_slug}/'),
            '/profile/<str:username>/':
            self.client.get(f'/profile/{test_username}/'),
            '/posts/<int:post_id>/':
            self.client.get(f'/posts/{test_post_id}/'),
        }
        for url, response in url_response_dict.items():
            with self.subTest(url=url):
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_url_at_desired_location_authorized(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_at_desired_location_author(self):
        test_post_id = PostsURLTests.test_post.id
        response = self.author_client.get(f'/posts/{test_post_id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_url_redirect_anonymous_on_login(self):
        response = self.client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_post_edit_url_redirect_nonauthor_on_post_detail(self):
        test_post_id = PostsURLTests.test_post.id
        response = self.authorized_client.get(f'/posts/{test_post_id}/edit/')
        expected_url = f'/posts/{test_post_id}/'
        self.assertRedirects(response, expected_url)

    def test_add_comment_only_for_authorized(self):
        test_post_id = PostsURLTests.test_post.id
        add_comment_url = f'/posts/{test_post_id}/comment/'
        login_url = '/auth/login/'
        redirect_login_url = (
            login_url + '?next=' + add_comment_url
        )
        response = self.client.post(
            add_comment_url,
            data={'text': 'Тестовый комментарий'},
            follow=True
        )
        self.assertRedirects(response, redirect_login_url)
