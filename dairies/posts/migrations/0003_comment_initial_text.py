# Generated by Django 2.2.16 on 2023-05-02 20:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0002_auto_20230502_1952'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='initial_text',
            field=models.TextField(blank=True, verbose_name='Изначальный текст комментария'),
        ),
    ]