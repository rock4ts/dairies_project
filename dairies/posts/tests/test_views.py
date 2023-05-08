import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, override_settings, TestCase
from django.urls import reverse

from posts.forms import CommentForm, PostForm
from posts.models import Comment, Follow, Group, Post
from posts.tests import utils_for_tests

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
        cls.test_random_user = User.objects.create_user(username='random_user')
        cls.test_group = Group.objects.create(
            title='Тестовое сообщество',
            description='Тестовое описание сообщества',
        )
        cls.test_image = utils_for_tests.create_test_image(
            'test_image', 'jpg'
        )
        for i in range(1, 14):
            Post.objects.create(
                text='Тестовый текст ' + str(i),
                author=cls.test_author,
                group=cls.test_group,
                image=cls.test_image
            )
        cls.test_post = Post.objects.latest('pub_date')
        cls.test_comment = Comment.objects.create(
            post=cls.test_post,
            author=cls.test_author,
            text='Тестовый комментарий',
        )
        cls.unauthorized_client = Client()
        cls.random_user_client = Client()
        cls.random_user_client.force_login(cls.test_random_user)
        cls.author_client = Client()
        cls.author_client.force_login(cls.test_author)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()

    def test_pages_reverse_use_correct_template(self):
        test_post_id = PostsViewsTests.test_post.id
        test_comment_id = PostsViewsTests.test_comment.id
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
            reverse(
                'posts:edit_comment', kwargs={'comment_id': test_comment_id}
            ): 'posts/create_post.html',
            reverse('posts:follow_index'):
            'posts/follow.html',
        }
        for url, template in url_template_names.items():
            with self.subTest(url=url):
                response = PostsViewsTests.author_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_index_view_show_correct_context(self):
        response = PostsViewsTests.unauthorized_client.get(
            reverse('posts:index')
        )
        page_post = response.context['page_obj'].object_list[0]  # get 1st post
        # first post on page is the latest created
        model_post = PostsViewsTests.test_post
        utils_for_tests.page_entry_equal_model_entry(
            self, Post, page_post, model_post
        )

    def test_index_view_context_subscriptions_key_value_is_correct(self):
        follower = PostsViewsTests.test_random_user
        author = PostsViewsTests.test_author
        subscribed_status = {'subscribed': True, 'unsubscribed': False}
        for status_name, status_value in subscribed_status.items():
            with self.subTest(status_name=status_name):
                if status_name == 'subscribed':
                    Follow.objects.create(user=follower, author=author)
                    response = PostsViewsTests.random_user_client.get(
                        reverse('posts:index')
                    )
                    has_subscriptions = response.context['has_subscriptions']
                    self.assertEqual(has_subscriptions, status_value)
                    Follow.objects.get(user=follower, author=author).delete()
                else:
                    response = PostsViewsTests.random_user_client.get(
                        reverse('posts:index')
                    )
                    has_subscriptions = response.context['has_subscriptions']
                    self.assertEqual(has_subscriptions, status_value)

    def test_group_posts_view_show_correct_context(self):
        test_group = PostsViewsTests.test_group
        test_slug = test_group.slug
        response = PostsViewsTests.unauthorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': test_slug})
        )
        # test context's page object with posts
        page_post = response.context['page_obj'].object_list[0]  # get 1st post
        # first post on page is the latest created
        model_post = test_group.posts.latest('pub_date')
        utils_for_tests.page_entry_equal_model_entry(
            self, Post, page_post, model_post
        )
        # test context's group object
        context_group = response.context['group']
        model_group = test_group
        utils_for_tests.page_entry_equal_model_entry(
            self, Group, context_group, model_group
        )
        # test that group_page variable is available and equal to True
        group_page = response.context['group_page']
        self.assertEqual(group_page, True)

    def test_profile_view_show_correct_context(self):
        profile_user = PostsViewsTests.test_author
        response = PostsViewsTests.unauthorized_client.get(
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
        utils_for_tests.page_entry_equal_model_entry(
            self, Post, page_post, model_post
        )
        # test context contains user whose profile page was requested
        context_author = response.context['author']
        self.assertEqual(context_author, profile_user)

    def test_profile_view_context_following_key_value_is_correct(self):
        follower = PostsViewsTests.test_random_user
        profile_user = PostsViewsTests.test_author
        subscribed_status = {'subscribed': True, 'unsubscribed': False}
        for status_name, status_value in subscribed_status.items():
            with self.subTest(status_name=status_name):
                if status_name == 'subscribed':
                    Follow.objects.create(user=follower, author=profile_user)
                    response = PostsViewsTests.random_user_client.get(
                        reverse(
                            'posts:profile',
                            kwargs={'username': profile_user.username}
                        )
                    )
                    following = response.context['following']
                    self.assertEqual(following, status_value)
                    Follow.objects.get(
                        user=follower,
                        author=profile_user
                    ).delete()
                else:
                    response = PostsViewsTests.random_user_client.get(
                        reverse(
                            'posts:profile',
                            kwargs={'username': profile_user.username}
                        )
                    )
                    following = response.context['following']
                    self.assertEqual(following, status_value)
        # test following value for unauthorised user is False
        response = PostsViewsTests.unauthorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': profile_user.username}
            )
        )
        following = response.context['following']
        self.assertEqual(following, False)

    def test_post_detail_view_show_correct_context(self):
        test_post = PostsViewsTests.test_post
        response = PostsViewsTests.unauthorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': test_post.id})
        )
        context_post = response.context['post']
        model_post = Post.objects.get(id=test_post.id)
        utils_for_tests.page_entry_equal_model_entry(
            self, Post, context_post, model_post
        )
        # test context contains CommentForm instance
        context_comment_form = response.context['form']
        self.assertIsInstance(context_comment_form, CommentForm)

        # test context also contains comments queryset
        context_post_comments = response.context['post_comments']
        self.assertIsInstance(
            context_post_comments.latest('pub_date'),
            Comment
        )

    def test_post_create_view_show_correct_context(self):
        response = PostsViewsTests.author_client.get(
            reverse('posts:post_create')
        )
        # test context form is instance of PostForm
        context_form = response.context['form']
        self.assertIsInstance(context_form, PostForm)

    def test_post_edit_view_show_correct_context_for_author(self):
        test_post_id = PostsViewsTests.test_post.id
        response = PostsViewsTests.author_client.get(
            reverse('posts:post_edit', kwargs={'post_id': test_post_id})
        )
        # test context form is instance of PostForm
        context_form = response.context['form']
        self.assertIsInstance(context_form, PostForm)
        # test 'is_edit' variable is in the context and True for author client
        expected_value = True
        is_edit = response.context['is_edit']
        self.assertEqual(is_edit, expected_value)

    def test_post_delete_view_deletes_post(self):
        new_test_post = Post.objects.create(
            text='Тестовый пост для удаления',
            author=PostsViewsTests.test_author,
            group=PostsViewsTests.test_group,
            image=PostsViewsTests.test_image
        )
        new_test_post_id = new_test_post.id
        new_test_post_created = Post.objects.filter(
            pk=new_test_post_id
        ).exists()
        self.assertEqual(new_test_post_created, True)
        PostsViewsTests.author_client.post(
            reverse(
                'posts:post_delete',
                kwargs={'post_id': new_test_post_id}
            )
        )
        new_test_post_deleted = not (
            Post.objects.filter(pk=new_test_post_id).exists()
        )
        self.assertEqual(new_test_post_deleted, True)

    def test_edit_comment_view_show_correct_context_for_author(self):
        test_comment_id = PostsViewsTests.test_comment.id
        response = PostsViewsTests.author_client.get(
            reverse(
                'posts:edit_comment', kwargs={'comment_id': test_comment_id}
            )
        )
        # test context contains CommentForm
        context_form = response.context['form']
        self.assertIsInstance(context_form, CommentForm)
        # test 'is_comment' variable is in the context and equal True
        expected_value = True
        is_comment = response.context['is_comment']
        self.assertEqual(is_comment, expected_value)

    def test_edit_comment_view_changes_is_edited_model_field(self):
        test_comment_id = PostsViewsTests.test_comment.id
        changes_statuses = {'not applied': False, 'applied': True}
        for status_name, expected_value in changes_statuses.items():
            with self.subTest(status_name=status_name):
                if status_name == 'applied':
                    form_data = {'text': 'changed comment text'}
                else:
                    form_data = {
                        'text': PostsViewsTests.test_comment.initial_text
                    }
                PostsViewsTests.author_client.post(
                    f'/dairies/comments/{test_comment_id}/edit/',
                    data=form_data,
                    follow=True
                )
                is_edited = Comment.objects.get(pk=test_comment_id).is_edited
                self.assertEqual(is_edited, expected_value)

    def test_comment_delete_view_deletes_comment(self):
        new_test_comment = Comment.objects.create(
            text='Тестовый комментарий для удаления',
            post=PostsViewsTests.test_post,
            author=PostsViewsTests.test_author,
        )
        new_test_comment_id = new_test_comment.id
        new_test_comment_created = Comment.objects.filter(
            pk=new_test_comment_id
        ).exists()
        self.assertEqual(new_test_comment_created, True)
        PostsViewsTests.author_client.post(
            reverse(
                'posts:delete_comment',
                kwargs={'comment_id': new_test_comment_id}
            )
        )
        new_test_comment_deleted = not (
            Comment.objects.filter(pk=new_test_comment_id).exists()
        )
        self.assertEqual(new_test_comment_deleted, True)

    def test_index_view_first_page_contains_correct_number_of_records(self):
        # use function that returns expected number of posts based on page
        expected_number_of_posts = utils_for_tests.posts_number_on_page(1)
        response = PostsViewsTests.author_client.get(
            reverse('posts:index')
        )
        self.assertEqual(
            len(response.context['page_obj'].object_list),
            expected_number_of_posts
        )

    def test_index_view_second_page_contains_correct_number_of_records(self):
        expected_number_of_posts = utils_for_tests.posts_number_on_page(2)
        response = PostsViewsTests.author_client.get(
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
        PostsViewsTests.author_client.post(
            reverse('posts:post_create'),
            data=create_form_data,
            follow=True
        )
        response_added_post = PostsViewsTests.unauthorized_client.get(
            reverse('posts:index')
        )
        Post.objects.get(text='Кэш пост').delete()
        response_deleted_post = PostsViewsTests.unauthorized_client.get(
            reverse('posts:index')
        )
        self.assertEqual(
            response_added_post.content,
            response_deleted_post.content
        )
        cache.clear()
        response_cache_clear = PostsViewsTests.unauthorized_client.get(
            reverse('posts:index')
        )
        self.assertNotEqual(
            response_added_post.content,
            response_cache_clear.content
        )

    def test_group_posts_view_first_page_has_correct_number_of_records(self):
        expected_number_of_posts = utils_for_tests.posts_number_on_page(1)
        test_slug = PostsViewsTests.test_group.slug
        response = PostsViewsTests.author_client.get(
            reverse('posts:group_posts', kwargs={'slug': test_slug})
        )
        self.assertEqual(
            len(response.context['page_obj'].object_list),
            expected_number_of_posts
        )

    def test_group_posts_view_second_page_has_correct_number_of_records(self):
        expected_number_of_posts = utils_for_tests.posts_number_on_page(2)
        test_slug = PostsViewsTests.test_group.slug
        response = PostsViewsTests.author_client.get(
            reverse('posts:group_posts', kwargs={'slug': test_slug})
            + '?page=2'
        )
        self.assertEqual(
            len(response.context['page_obj'].object_list),
            expected_number_of_posts
        )

    def test_profile_view_first_page_contains_correct_number_of_records(self):
        expected_number_of_posts = utils_for_tests.posts_number_on_page(1)
        profile_user = PostsViewsTests.test_author
        response = PostsViewsTests.author_client.get(
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
        expected_number_of_posts = utils_for_tests.posts_number_on_page(2)
        profile_user = PostsViewsTests.test_author
        response = PostsViewsTests.author_client.get(
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

    def test_post_detail_view_show_added_comment(self):
        comment_form_data = {'text': 'Тестовый комментарий'}
        test_post = PostsViewsTests.test_post
        number_of_comments_before_new = test_post.comments.count()
        PostsViewsTests.author_client.post(
            reverse('posts:add_comment', kwargs={'post_id': test_post.id}),
            data=comment_form_data,
            follow=True
        )
        response = PostsViewsTests.unauthorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': test_post.id})
        )
        number_of_comments_after_new = (
            response.context['post_comments'].count()
        )
        self.assertEqual(
            number_of_comments_after_new,
            number_of_comments_before_new + 1
        )

    def test_profile_follow_for_authorized(self):
        followed_user = PostsViewsTests.test_user_for_follow
        follow_ids_before_new = list(
            Follow.objects.values_list('id', flat=True)
        )
        follows_count = (
            Follow.objects.count()
        )
        follow_response = PostsViewsTests.author_client.post(
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
        duplicate_follow_response = PostsViewsTests.author_client.post(
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
        follow_response = PostsViewsTests.author_client.post(
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
        follow_response = PostsViewsTests.author_client.post(
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
        PostsViewsTests.author_client.post(
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
        PostsViewsTests.author_client.post(
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
        follower_index_response = PostsViewsTests.author_client.get(
            reverse(
                'posts:follow_index'
            )
        )
        non_follower_index_response = PostsViewsTests.random_user_client.get(
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
