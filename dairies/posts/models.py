from django.contrib.auth import get_user_model
from django.db import models

from core.models import PubDateModel
from pytils.translit import slugify

User = get_user_model()


class Post(PubDateModel):
    text = models.TextField(
        verbose_name='Текст записи',
        help_text='Здесь должно быть что-то содержательное',
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='posts'
    )
    group = models.ForeignKey(
        'Group',
        verbose_name='Тема',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
    )
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return self.text[:15]


class Group(models.Model):
    title = models.CharField(
        verbose_name='Название темы',
        max_length=200
    )
    slug = models.SlugField(
        'Слаг темы',
        max_length=100,
        unique=True,
        blank=True
    )
    description = models.TextField(
        verbose_name='Краткое описание темы'
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:100]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Comment(PubDateModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField(
        verbose_name='Текст комментария',
    )
    initial_text = models.TextField(
        verbose_name='Изначальный текст комментария',
        blank=True
    )
    is_edited = models.BooleanField(default=False)

    class Meta:
        ordering = ['-pub_date']

    def save(self, *args, **kwargs):
        self.initial_text = self.text
        super().save(*args, **kwargs)

    def __str__(self):
        return 'Комментарий'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='following',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_constraint_fail',
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='Пользователь не может подписаться сам на себя'
            ),
        ]
