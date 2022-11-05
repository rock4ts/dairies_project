import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import override_settings, TestCase
from django.urls import reverse

from posts.models import Comment, Post, Group
from posts.tests import posts_test_utils

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_author = User.objects.create_user(username='rock4ts')
        cls.test_group = Group.objects.create(
            title='Тестовая группа post_create',
            description='Описание тестовой группы post_create'
        )
        cls.test_group_for_updates = Group.objects.create(
            title='Тестовая группа post_edit',
            description='Описание тестовой группы post_edit',
        )
        cls.test_post = Post.objects.create(
            text='Тестовый текст',
            author=PostsFormsTests.test_author,
            group=PostsFormsTests.test_group,
            image=posts_test_utils.create_test_image(
                'test_image', 'gif'
            )
        )
        cls.test_comment = Comment.objects.create(
            post=PostsFormsTests.test_post,
            author=PostsFormsTests.test_author,
            text='Тестовый комментарий',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.author_client = self.client
        self.author_client.force_login(PostsFormsTests.test_author)

    def test_create_post(self):
        posts_count = Post.objects.count()
        post_ids_before_create = list(
            Post.objects.values_list('id', flat=True)
        )
        create_form_data = {
            'text': 'Тестовая запись из формы',
            'group': PostsFormsTests.test_group.id,
            'image': posts_test_utils.create_test_image(
                'create_post_image', 'gif'
            )
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=create_form_data,
            follow=True
        )
        created_post = Post.objects.exclude(id__in=post_ids_before_create)[0]
        self.assertEqual(
            created_post.text,
            create_form_data['text']
        )
        self.assertEqual(
            created_post.group.id,
            create_form_data['group']
        )
        self.assertEqual(
            created_post.image.name.split('/')[-1],
            create_form_data['image'].__dict__['_name']
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        post_author = response.wsgi_request.user
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': post_author.username})
        )

    def test_edit_post(self):
        test_post_for_edit = Post.objects.create(
            text='Тестовый текст',
            author=PostsFormsTests.test_author,
            group=PostsFormsTests.test_group,
            image=posts_test_utils.create_test_image(
                'create_post_image', 'gif'
            )
        )
        posts_count = Post.objects.count()
        edit_form_data = {
            'text': 'Изменённый тестовый текст',
            'group': PostsFormsTests.test_group_for_updates.id,
            'image': posts_test_utils.create_test_image(
                'edit_post_image', 'gif'
            ),
        }
        # check initial post data is not equal to form data
        self.assertNotEqual(
            test_post_for_edit.text,
            edit_form_data['text']
        )
        self.assertNotEqual(
            test_post_for_edit.group.id,
            edit_form_data['group']
        )
        self.assertNotEqual(
            test_post_for_edit.image.name.split('/')[-1],
            edit_form_data['image'].__dict__['_name']
        )
        response = self.author_client.post(
            reverse(
                'posts:post_edit', kwargs={'post_id': test_post_for_edit.id}
            ),
            data=edit_form_data,
            follow=True
        )
        test_post_after_edit = Post.objects.get(pk=test_post_for_edit.id)
        self.assertEqual(Post.objects.count(), posts_count)
        # check editted post data is equal to form data
        self.assertEqual(
            test_post_after_edit.text,
            edit_form_data['text']
        )
        self.assertEqual(
            test_post_after_edit.group.id,
            edit_form_data['group']
        )
        self.assertEqual(
            test_post_after_edit.image.name.split('/')[-1],
            edit_form_data['image'].__dict__['_name']
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail', kwargs={'post_id': test_post_for_edit.id}
            )
        )

    def test_add_comment(self):
        test_post_id = PostsFormsTests.test_post.id
        comments_count = Comment.objects.count()
        comment_ids_before_new = list(
            Comment.objects.values_list('id', flat=True)
        )
        comment_form_data = {
            'text': 'Тестовый комментарий из формы',
        }
        response = self.author_client.post(
            reverse('posts:add_comment', kwargs={'post_id': test_post_id}),
            data=comment_form_data,
            follow=True
        )
        new_comment = Comment.objects.exclude(id__in=comment_ids_before_new)[0]
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(
            new_comment.text,
            comment_form_data['text']
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': test_post_id})
        )
