from django.contrib import admin

from .models import Comment, Follow, Group, Post


class AdminPost(admin.ModelAdmin):
    list_display = ('pk', 'text', 'pub_date', 'author', 'group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'
    list_editable = ('group',)


class AdminComment(admin.ModelAdmin):
    list_display = ('pk', 'text', 'pub_date', 'author', 'post',)
    search_fields = ('text',)
    list_filter = ('author', 'pub_date',)
    empty_value_display = '-пусто-'


class AdminFollow(admin.ModelAdmin):
    list_display = ('pk', 'author', 'user',)
    list_filter = ('user', 'author',)


admin.site.register(Post, AdminPost)
admin.site.register(Group)
admin.site.register(Comment, AdminComment)
admin.site.register(Follow, AdminFollow)
