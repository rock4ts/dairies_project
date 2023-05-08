from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Comment, Follow, Group, Post

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
        cls.test_comment = Comment.objects.create(
            post=cls.test_post,
            author=cls.test_author,
            text='Тестовый комментарий',
        )
        cls.test_follow = Follow.objects.create(
            user=cls.test_nonauthor,
            author=cls.test_author,
        )
        cls.author_client = Client()
        cls.author_client.force_login(cls.test_author)
        cls.random_authorized_client = Client()
        cls.random_authorized_client.force_login(cls.test_nonauthor)

    def test_pages_use_correct_template(self):
        test_post_id = PostsURLTests.test_post.id
        test_comment_id = PostsURLTests.test_comment.id
        test_slug = PostsURLTests.test_group.slug
        test_username = PostsURLTests.test_author.username
        prefix = '/dairies/'
        url_template_names = {
            '': 'posts/index.html',
            f'group/{test_slug}/': 'posts/group_list.html',
            f'profile/{test_username}/': 'posts/profile.html',
            f'posts/{test_post_id}/': 'posts/post_detail.html',
            'create/': 'posts/create_post.html',
            f'posts/{test_post_id}/edit/': 'posts/create_post.html',
            f'comments/{test_comment_id}/edit/': 'posts/create_post.html',
            'follow/': 'posts/follow.html',
            '404_page': 'core/404.html',
        }
        for url, template in url_template_names.items():
            with self.subTest(url=url):
                response = self.author_client.get(prefix + url)
                self.assertTemplateUsed(response, template)

    def test_no_login_urls_at_desired_locations(self):
        test_slug = PostsURLTests.test_group.slug
        test_post_id = PostsURLTests.test_post.id
        test_username = PostsURLTests.test_author.username
        url_response_dict = {
            '/dairies/':
            self.client.get('/dairies/'),
            '/dairies/group/<slug:slug>/':
            self.client.get(f'/dairies/group/{test_slug}/'),
            '/dairies/profile/<str:username>/':
            self.client.get(f'/dairies/profile/{test_username}/'),
            '/dairies/posts/<int:post_id>/':
            self.client.get(f'/dairies/posts/{test_post_id}/'),
        }
        for url, response in url_response_dict.items():
            with self.subTest(url=url):
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page_returns_404(self):
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_create_url_at_desired_location(self):
        response = PostsURLTests.random_authorized_client.get(
            '/dairies/create/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_and_delete_urls_at_desired_locations(self):
        test_post_id = PostsURLTests.test_post.id
        request_commands = ['edit', 'delete']
        for command in request_commands:
            with self.subTest(command=command):
                response = PostsURLTests.author_client.get(
                    f'/dairies/posts/{test_post_id}/{command}/', follow=True
                )
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_url_redirect_anonymous_on_login(self):
        create_post_url = '/dairies/create/'
        login_url = '/dairies/auth/login/'
        response = self.client.get(f'{create_post_url}', follow=True)
        self.assertRedirects(
            response,
            login_url + '?next=' + create_post_url
        )

    def test_post_edit_and_delete_urls_redirect_nonauthor_on_post_detail(self):
        test_post_id = PostsURLTests.test_post.id
        expected_url = f'/dairies/posts/{test_post_id}/'
        request_commands = ['edit', 'delete']
        for command in request_commands:
            with self.subTest(command=command):
                response = PostsURLTests.random_authorized_client.get(
                    f'/dairies/posts/{test_post_id}/{command}/'
                )
                self.assertRedirects(response, expected_url)

    def test_post_edit_and_delete_urls_redirect_correctly(self):
        test_post_id = PostsURLTests.test_post.id
        test_author_username = PostsURLTests.test_author.username
        commands_redirect_url = {
            'edit':
            f'/dairies/posts/{test_post_id}/',
            'delete':
            f'/dairies/profile/{test_author_username}/',
        }
        for command, redirect_url in commands_redirect_url.items():
            with self.subTest(command=command):
                if command == 'edit':
                    form_data = {'text': 'changed post text'}
                    response = PostsURLTests.author_client.post(
                        f'/dairies/posts/{test_post_id}/{command}/',
                        form_data
                    )
                else:
                    response = PostsURLTests.author_client.post(
                        f'/dairies/posts/{test_post_id}/{command}/',
                        follow=True
                    )
                self.assertRedirects(response, redirect_url)

    def test_add_comment_url_at_desired_location(self):
        test_post_id = PostsURLTests.test_post.id
        response = PostsURLTests.random_authorized_client.get(
            f'/dairies/posts/{test_post_id}/comment/', follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_comment_edit_and_delete_urls_at_desired_locations(self):
        test_comment_id = PostsURLTests.test_comment.id
        request_commands = ['edit', 'delete']
        for command in request_commands:
            with self.subTest(command=command):
                response = PostsURLTests.author_client.get(
                    f'/dairies/comments/{test_comment_id}/{command}/',
                    follow=True
                )
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_add_comment_url_redirect_on_login(self):
        test_post_id = PostsURLTests.test_post.id
        add_comment_url = f'/dairies/posts/{test_post_id}/comment/'
        login_url = '/dairies/auth/login/'
        redirect_login_url = (login_url + '?next=' + add_comment_url)
        response = self.client.get(add_comment_url)
        self.assertRedirects(response, redirect_login_url)

    def test_edit_and_delete_comment_urls_redirect_nonauthor_on_post_detail(
            self):
        test_comment_id = PostsURLTests.test_comment.id
        test_post_id = PostsURLTests.test_post.id
        expected_url = f'/dairies/posts/{test_post_id}/'
        request_commands = ['edit', 'delete']
        for command in request_commands:
            with self.subTest(command=command):
                response = PostsURLTests.random_authorized_client.get(
                    f'/dairies/comments/{test_comment_id}/{command}/'
                )
                self.assertRedirects(response, expected_url)

    def test_edit_and_delete_comment_urls_redirect_correctly(self):
        test_post_id = PostsURLTests.test_post.id
        test_comment_id = PostsURLTests.test_comment.id
        commands = ['edit', 'delete']
        redirect_url = f'/dairies/posts/{test_post_id}/'
        for command in commands:
            with self.subTest(command=command):
                if command == 'edit':
                    form_data = {'text': 'changed comment text'}
                    response = PostsURLTests.author_client.post(
                        f'/dairies/comments/{test_comment_id}/{command}/',
                        form_data,
                        follow=True
                    )
                else:
                    response = PostsURLTests.author_client.post(
                        f'/dairies/comments/{test_post_id}/{command}/',
                        follow=True
                    )
                self.assertRedirects(response, redirect_url)

    def test_follow_index_url_at_desired_location(self):
        response = PostsURLTests.random_authorized_client.get(
            '/dairies/follow/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_follow_and_unfollow_urls_at_desired_locations(self):
        request_commands = ['follow', 'unfollow']
        followed_author_username = PostsURLTests.test_author.username
        for command in request_commands:
            with self.subTest(command=command):
                response = PostsURLTests.random_authorized_client.get(
                    f'/dairies/profile/{followed_author_username}/{command}/',
                    follow=True
                )
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_follow_urls_redirect_on_login(self):
        author = PostsURLTests.test_author
        follow_urls = [
            '/dairies/follow/',
            f'/dairies/profile/{author}/follow/',
            f'/dairies/profile/{author}/unfollow/'
        ]
        login_url = '/dairies/auth/login/'
        for url in follow_urls:
            with self.subTest(url=url):
                redirect_login_url = login_url + '?next=' + url
                response = self.client.get(url)
                self.assertRedirects(response, redirect_login_url)

    def test_follow_urls_redirect_correctly(self):
        request_commands = ['follow', 'unfollow']
        followed_author_username = PostsURLTests.test_author.username
        redirect_url = f'/dairies/profile/{followed_author_username}/'
        for command in request_commands:
            with self.subTest(command=command):
                response = PostsURLTests.random_authorized_client.post(
                    f'/dairies/profile/{followed_author_username}/{command}/',
                    follow=True
                )
                self.assertRedirects(response, redirect_url)
