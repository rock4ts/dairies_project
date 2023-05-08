from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.test import TestCase

from posts.models import Comment, Follow, Group, Post

User = get_user_model()


class PostsModelsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_group = Group.objects.create(
            title='Ж' * 100,
            description='Тестовое описание',
        )
        cls.test_user = User.objects.create_user(username='rock4ts')
        cls.test_author = (
            User.objects.create_user(username='Celebrity')
        )
        cls.test_post = Post.objects.create(
            author=cls.test_user,
            text='Тестовый пост',
        )
        cls.test_comment = Comment.objects.create(
            post=cls.test_post,
            author=cls.test_user,
            text='Тестовый комментарий',
        )

    def test_post_model_has_correct_object_name(self):
        test_post_name = str(PostsModelsTest.test_post)
        expected_post_name = PostsModelsTest.test_post.text[:15]
        self.assertEqual(test_post_name, expected_post_name)

    def test_post_model_has_correct_verbose_names(self):
        test_post = PostsModelsTest.test_post
        field_verboses = {
            'text': 'Текст записи',
            'group': 'Тема',
            'image': 'Изображение',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    test_post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_post_model_help_text(self):
        test_post = PostsModelsTest.test_post
        expected_value = 'Здесь должно быть что-то содержательное'
        self.assertEqual(
            test_post._meta.get_field('text').help_text,
            expected_value
        )

    def test_group_model_have_correct_object_name(self):
        test_group_name = str(PostsModelsTest.test_group)
        expected_group_name = PostsModelsTest.test_group.title
        self.assertEqual(test_group_name, expected_group_name)

    def test_group_model_has_correct_verbose_names(self):
        test_group = PostsModelsTest.test_group
        field_verboses = {
            'title': 'Название темы',
            'slug': 'Слаг темы',
            'description': 'Краткое описание темы',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    test_group._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_group_model_converts_title_to_slug(self):
        group = PostsModelsTest.test_group
        slug = group.slug
        self.assertEqual(slug, 'zh' * 50)

    def test_group_model_slug_max_length_not_exceed(self):
        group = PostsModelsTest.test_group
        max_length_slug = group._meta.get_field('slug').max_length
        length_slug = len(group.slug)
        self.assertEqual(max_length_slug, length_slug)

    def test_comment_model_have_correct_object_name(self):
        test_comment_name = str(PostsModelsTest.test_comment)
        expected_comment_name = 'Комментарий'
        self.assertEqual(test_comment_name, expected_comment_name)

    def test_comment_model_has_correct_verbose_names(self):
        test_comment = PostsModelsTest.test_comment
        field_verboses = {
            'text': 'Текст комментария',
            'initial_text': 'Изначальный текст комментария',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    test_comment._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_comment_model_fills_initial_text_field_with_text_field(self):
        comment = PostsModelsTest.test_comment
        text = comment.text
        initial_text = comment.initial_text
        self.assertEqual(text, initial_text)

    def test_follow_model_has_correct_verbose_names(self):
        follow_instance = Follow.objects.create(
            user=PostsModelsTest.test_user,
            author=PostsModelsTest.test_author,
        )
        field_verboses = {
            'user': 'Подписчик',
            'author': 'Автор',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    follow_instance._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_follow_model_applies_unique_constraints(self):
        following_user = PostsModelsTest.test_user
        followed_user = PostsModelsTest.test_author
        try:
            Follow.objects.create(user=following_user, author=followed_user)
            Follow.objects.create(user=following_user, author=followed_user)
        except Exception as err:
            self.assertIsInstance(err, IntegrityError)

    def test_no_self_follow(self):
        following_user = PostsModelsTest.test_author
        constraint_name = 'Пользователь не может подписаться сам на себя'
        with self.assertRaisesMessage(IntegrityError, constraint_name):
            Follow.objects.create(user=following_user, author=following_user)
