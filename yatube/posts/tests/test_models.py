from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.test import TestCase

from posts.models import Follow, Group, Post

User = get_user_model()


class PostsModelsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание',
        )
        cls.test_author = User.objects.create_user(username='rock4ts')
        cls.test_author_for_follow = (
            User.objects.create_user(username='Celebrity')
        )
        cls.test_post = Post.objects.create(
            author=cls.test_author,
            text='Тестовый пост',
        )

    def setUp(self):
        self.authorized_client = self.client
        self.test_author = PostsModelsTest.test_author
        self.authorized_client.force_login(self.test_author)

    def test_post_model_have_correct_object_name(self):
        test_post_name = str(PostsModelsTest.test_post)
        expected_post_name = PostsModelsTest.test_post.text[:15]
        self.assertEqual(test_post_name, expected_post_name)

    def test_group_model_have_correct_object_name(self):
        test_group_name = str(PostsModelsTest.test_group)
        expected_group_name = PostsModelsTest.test_group.title
        self.assertEqual(test_group_name, expected_group_name)

    def test_verbose_names(self):
        test_post = PostsModelsTest.test_post
        field_verboses = {
            'text': 'Текст записи',
            'group': 'Сообщество',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    test_post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_help_text(self):
        test_post = PostsModelsTest.test_post
        expected_value = 'Здесь должно быть что-то содержательное'
        self.assertEqual(
            test_post._meta.get_field('text').help_text,
            expected_value
        )

    def test_no_self_follow(self):
        following_user = PostsModelsTest.test_author
        constraint_name = 'Пользователь не может подписаться сам на себя'
        with self.assertRaisesMessage(IntegrityError, constraint_name):
            Follow.objects.create(user=following_user, author=following_user)
