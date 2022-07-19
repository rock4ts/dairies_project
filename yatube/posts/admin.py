from django.contrib import admin

from .models import Comment, Group, Post


class AdminPost(admin.ModelAdmin):
    list_display = ('pk', 'text', 'pub_date', 'author', 'group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'
    list_editable = ('group',)


class AdminComment(admin.ModelAdmin):
    list_display = ('post', 'author', 'text', 'pub_date',)
    search_fields = ('text',)
    list_filter = ('pub_date', 'author',)
    empty_value_display = '-пусто-'


admin.site.register(Post, AdminPost)
admin.site.register(Group)
admin.site.register(Comment, AdminComment)
