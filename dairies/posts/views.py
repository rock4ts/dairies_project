from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User
from .utils import create_page_obj


def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.select_related('group', 'author').all()
    page_obj = create_page_obj(request, post_list)
    if not request.user.is_anonymous:
        has_subscriptions = Follow.objects.filter(user=request.user).exists()
    else:
        has_subscriptions = False
    context = {
        'page_obj': page_obj,
        'has_subscriptions': has_subscriptions,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    group_page = True
    post_list = group.posts.all()
    page_obj = create_page_obj(request, post_list)
    context = {
        'group': group,
        'group_page': group_page,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    user = get_object_or_404(User, username=username)
    post_list = user.posts.all()
    page_obj = create_page_obj(request, post_list)
    following = (
        request.user.is_authenticated
        and Follow.objects.filter(
            user=request.user,
            author__username=username
        ).exists()
    )
    context = {
        'author': user,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    post_comments = post.comments.all()
    context = {
        'post': post,
        'form': CommentForm(),
        'post_comments': post_comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    form.instance.author = request.user
    if form.is_valid():
        form.save()
        username = request.user.username
        return redirect('posts:profile', username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post_data = get_object_or_404(Post, pk=post_id)
    if request.user != post_data.author:
        return redirect('posts:post_detail', post_id)
    is_edit = True
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post_data
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'is_edit': is_edit
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    post.delete()
    username = post.author.username
    return redirect('posts:profile', username)


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = Post.objects.get(id=post_id)
        comment.save()
    return redirect('posts:post_detail', post_id)


@login_required
def edit_comment(request, comment_id):
    comment_data = get_object_or_404(Comment, pk=comment_id)
    post_id = comment_data.post.pk
    if request.user != comment_data.author:
        return redirect('posts:post_detail', post_id)
    form = CommentForm(request.POST or None, instance=comment_data)
    if form.is_valid():
        comment = form.save(commit=False)
        if comment.text != comment.initial_text:
            comment.is_edited = True
        comment.save()
        return redirect('posts:post_detail', post_id)
    is_comment = True
    context = {
        'form': form,
        'is_comment': is_comment
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    post_id = comment.post.pk
    if request.user != comment.author:
        return redirect('posts:post_detail', post_id)
    comment.delete()
    return redirect('posts:post_detail', post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = create_page_obj(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    viewed_profile = get_object_or_404(User, username=username)
    if request.user == viewed_profile:
        return redirect('posts:profile', username)
    Follow.objects.get_or_create(
        user=request.user,
        author=viewed_profile
    )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    get_object_or_404(
        Follow, user=request.user, author__username=username
    ).delete()
    return redirect('posts:profile', username)
