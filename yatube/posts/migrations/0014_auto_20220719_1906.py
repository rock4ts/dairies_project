# Generated by Django 2.2.16 on 2022-07-19 19:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0013_auto_20220718_2346'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='follow',
            name='Проверка уникальности подписки',
        ),
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(fields=('user', 'author'), name='Пользователь уже подписан на данного автора'),
        ),
    ]