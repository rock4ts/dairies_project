import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, override_settings, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Follow, Group, Post
from posts.tests import posts_test_utils

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_author = User.objects.create_user(username='rock4ts')
        cls.test_user_for_follow = (
            User.objects.create_user(username='Celebrity')
        )
        cls.some_user = User.objects.create_user(username='random_user')
        cls.test_group = Group.objects.create(
            title='Тестовое сообщество',
            description='Тестовое описание сообщества',
        )
        cls.test_image = posts_test_utils.create_test_image(
            'test_image', 'jpg'
        )
        for i in range(1, 14):
            Post.objects.create(
                text='Тестовый текст ' + str(i),
                author=cls.test_author,
                group=cls.test_group,
                image=cls.test_image
            )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.unauthorized_client = self.client
        self.author_client = Client()
        self.author = PostsViewsTests.test_author
        self.author_client.force_login(self.author)
        self.some_user_client = Client()
        self.some_user = PostsViewsTests.some_user
        self.some_user_client.force_login(self.some_user)
        cache.clear()

    def test_pages_use_correct_template(self):
        test_post_id = Post.objects.latest('pub_date').id
        test_slug = PostsViewsTests.test_group.slug
        test_username = PostsViewsTests.test_author.username
        url_template_names = {
            reverse('posts:index'):
            'posts/index.html',
            reverse('posts:group_posts', kwargs={'slug': test_slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': test_username}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': test_post_id}):
            'posts/post_detail.html',
            reverse('posts:post_create'):
            'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': test_post_id}):
            'posts/create_post.html',
        }
        for url, template in url_template_names.items():
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_index_view_show_correct_context(self):
        response = self.author_client.get(
            reverse('posts:index')
        )
        page_post = response.context['page_obj'].object_list[0]  # get 1st post
        # first post on page is the latest created
        model_post = Post.objects.latest('pub_date')
        posts_test_utils.page_entry_equal_model_entry(
            self, Post, page_post, model_post
        )

    def test_index_view_first_page_contains_correct_number_of_records(self):
        # use function that returns expected number of posts based on page
        expected_number_of_posts = posts_test_utils.posts_number_on_page(1)
        response = self.author_client.get(
            reverse('posts:index')
        )
        self.assertEqual(
            len(response.context['page_obj'].object_list),
            expected_number_of_posts
        )

    def test_index_view_second_page_contains_correct_number_of_records(self):
        expected_number_of_posts = posts_test_utils.posts_number_on_page(2)
        response = self.author_client.get(
            reverse('posts:index') + '?page=2'
        )
        self.assertEqual(
            len(response.context['page_obj'].object_list),
            expected_number_of_posts
        )

    def test_index_view_uses_cache(self):
        create_form_data = {
            'text': 'Кэш пост',
        }
        self.author_client.post(
            reverse('posts:post_create'),
            data=create_form_data,
            follow=True
        )
        response_added_post = self.client.get(
            reverse('posts:index')
        )
        Post.objects.get(text='Кэш пост').delete()
        response_deleted_post = self.client.get(
            reverse('posts:index')
        )
        self.assertEqual(
            response_added_post.content,
            response_deleted_post.content
        )
        cache.clear()
        response_cache_clear = self.client.get(
            reverse('posts:index')
        )
        self.assertNotEqual(
            response_added_post.content,
            response_cache_clear.content
        )

    def test_group_posts_view_show_correct_context(self):
        test_group = PostsViewsTests.test_group
        test_slug = test_group.slug
        response = self.author_client.get(
            reverse('posts:group_posts', kwargs={'slug': test_slug})
        )
        # test context's page object with posts
        page_post = response.context['page_obj'].object_list[0]  # get 1st post
        # first post on page is the latest created
        model_post = test_group.posts.latest('pub_date')
        posts_test_utils.page_entry_equal_model_entry(
            self, Post, page_post, model_post
        )
        # test context's group object
        context_group = response.context['group']
        model_group = test_group
        posts_test_utils.page_entry_equal_model_entry(
            self, Group, context_group, model_group
        )

    def test_group_posts_view_first_page_has_correct_number_of_records(self):
        expected_number_of_posts = posts_test_utils.posts_number_on_page(1)
        test_slug = PostsViewsTests.test_group.slug
        response = self.author_client.get(
            reverse('posts:group_posts', kwargs={'slug': test_slug})
        )
        self.assertEqual(
            len(response.context['page_obj'].object_list),
            expected_number_of_posts
        )

    def test_group_posts_view_second_page_has_correct_number_of_records(self):
        expected_number_of_posts = posts_test_utils.posts_number_on_page(2)
        test_slug = PostsViewsTests.test_group.slug
        response = self.author_client.get(
            reverse('posts:group_posts', kwargs={'slug': test_slug})
            + '?page=2'
        )
        self.assertEqual(
            len(response.context['page_obj'].object_list),
            expected_number_of_posts
        )

    def test_profile_view_show_correct_context(self):
        profile_user = PostsViewsTests.test_author
        response = self.author_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': profile_user.username}
            )
        )
        # test context page object with profile posts
        page_post = response.context['page_obj'].object_list[0]
        # get 1st post on page
        model_post = (
            Post.objects.filter(author=profile_user).latest('pub_date')
        )
        # first post on page is the latest created
        posts_test_utils.page_entry_equal_model_entry(
            self, Post, page_post, model_post
        )
        # text context user object
        context_user = response.context['user']
        self.assertEqual(context_user, profile_user)

    def test_profile_view_first_page_contains_correct_number_of_records(self):
        expected_number_of_posts = posts_test_utils.posts_number_on_page(1)
        profile_user = PostsViewsTests.test_author
        response = self.author_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': profile_user.username}
            )
        )
        self.assertEqual(
            len(response.context['page_obj'].object_list),
            expected_number_of_posts
        )

    def test_profile_view_second_page_contains_correct_number_of_records(self):
        expected_number_of_posts = posts_test_utils.posts_number_on_page(2)
        profile_user = PostsViewsTests.test_author
        response = self.author_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': profile_user.username}
            )
            + '?page=2'
        )
        self.assertEqual(
            len(response.context['page_obj'].object_list),
            expected_number_of_posts
        )

    def test_post_detail_view_show_correct_context(self):
        test_post_id = Post.objects.latest('pub_date').id
        response = self.author_client.get(
            reverse('posts:post_detail', kwargs={'post_id': test_post_id})
        )
        context_post = response.context['post']
        model_post = Post.objects.get(id=test_post_id)
        posts_test_utils.page_entry_equal_model_entry(
            self, Post, context_post, model_post
        )

    def test_post_detail_view_show_correct_added_comment(self):
        comment_form_data = {'text': 'Тестовый комментарий'}
        test_post = Post.objects.latest('pub_date')
        comment_ids_before_new = list(
            test_post.comments.values_list('id', flat=True)
        )
        self.author_client.post(
            reverse('posts:add_comment', kwargs={'post_id': test_post.id}),
            data=comment_form_data,
            follow=True
        )
        response = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': test_post.id})
        )
        model_comment = test_post.comments.exclude(
            id__in=comment_ids_before_new
        )[0]
        context_comment = (
            response.context['post_comments'].get(id=model_comment.id)
        )
        posts_test_utils.page_entry_equal_model_entry(
            self, Comment, context_comment, model_comment
        )

    def test_post_create_view_show_correct_context(self):
        response = self.author_client.get(
            reverse('posts:post_create')
        )
        # test context form fields are instances of PostForm field classes
        posts_test_utils.context_form_fields_are_instances(
            self, response, PostForm
        )

    def test_post_create_view_assigns_correct_group(self):
        form_data = {
            'text': 'Пост для Тестового сообщества',
            'group': PostsViewsTests.test_group.id,
        }
        # make new post, variable omitted to pass linting test
        self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        created_post = Post.objects.latest('pub_date')
        self.assertEqual(created_post.group, PostsViewsTests.test_group)

    def test_post_edit_view_show_correct_context_for_author(self):
        test_post_id = Post.objects.latest('pub_date').id
        response = self.author_client.get(
            reverse('posts:post_edit', kwargs={'post_id': test_post_id})
        )
        # test context form fields are instances of PostForm field classes
        posts_test_utils.context_form_fields_are_instances(
            self, response, PostForm
        )
        # test 'is_edit' variable equal True is in context for author client
        is_edit = response.context['is_edit']
        self.assertTrue(is_edit)

    def test_profile_follow_for_authorized(self):
        followed_user = PostsViewsTests.test_user_for_follow
        follow_ids_before_new = list(
            Follow.objects.values_list('id', flat=True)
        )
        follows_count = (
            Follow.objects.count()
        )
        follow_response = self.author_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': followed_user.username}
            )
        )
        new_follow = Follow.objects.exclude(id__in=follow_ids_before_new)[0]
        self.assertEqual(new_follow.user, follow_response.wsgi_request.user)
        self.assertEqual(new_follow.author, followed_user)
        self.assertEqual(
            Follow.objects.count(),
            follows_count + 1
        )
        # test request to create follow obj with same params fails
        follow_ids_before_duplicate = list(
            Follow.objects.values_list('id', flat=True)
        )
        duplicate_follow_response = self.author_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': followed_user.username}
            )
        )
        new_follow_created = (
            Follow.objects.exclude(id__in=follow_ids_before_duplicate)
        )
        filter_duplicate_follow = Follow.objects.filter(
            user=duplicate_follow_response.wsgi_request.user,
            author=followed_user
        )
        self.assertFalse(new_follow_created.exists())
        self.assertEqual(filter_duplicate_follow.count(), 1)
        self.assertTrue(new_follow == filter_duplicate_follow[0])

    def test_profile_follow_redirects_if_user_tries_to_follow_himself(self):
        following_user = PostsViewsTests.test_author
        follow_response = self.author_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': following_user.username}
            )
        )
        self.assertRedirects(
            follow_response,
            reverse(
                'posts:profile',
                kwargs={'username': following_user.username}
            )
        )

    def test_profile_unfollow_for_authorized(self):
        followed_user = PostsViewsTests.test_user_for_follow
        follow_response = self.author_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': followed_user.username}
            )
        )
        response_user = follow_response.wsgi_request.user
        # assert that follow post request created a follow entry
        self.assertTrue(
            Follow.objects.filter(
                user=response_user, author=followed_user
            ).exists()
        )
        self.author_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': followed_user.username}
            )
        )
        # assert that unfollow post request deleted entry from database
        self.assertFalse(
            Follow.objects.filter(
                user=response_user, author=followed_user
            ).exists()
        )

    def test_following_users_have_new_post_in_posts_feed(self):
        followed_user = PostsViewsTests.test_user_for_follow
        self.author_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': followed_user.username}
            )
        )
        self.assertFalse(Post.objects.filter(author=followed_user).exists())
        new_post_fow_followers = Post.objects.create(
            text='Сообщение для подписчиков',
            author=followed_user
        )
        follower_index_response = self.author_client.get(
            reverse(
                'posts:follow_index'
            )
        )
        non_follower_index_response = self.some_user_client.get(
            reverse(
                'posts:follow_index'
            )
        )
        self.assertFalse(
            Follow.objects.filter(
                user=non_follower_index_response.wsgi_request.user,
                author=followed_user
            )
        )
        follower_context = (
            follower_index_response.context['page_obj'].object_list
        )
        non_follower_context = (
            non_follower_index_response.context['page_obj'].object_list
        )
        self.assertIn(new_post_fow_followers, follower_context)
        self.assertNotIn(new_post_fow_followers, non_follower_context)
