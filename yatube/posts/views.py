from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post

POST_OBJ = 10
User = get_user_model()


def paginate_posts(request, post_list):
    paginator = Paginator(post_list, POST_OBJ)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


@cache_page(20)
def index(request):
    posts = Post.objects.select_related('group')[:POST_OBJ]
    post_list = Post.objects.all()
    page_obj = paginate_posts(request, post_list)
    context = {
        'page_obj': page_obj,
        'posts': posts,
        'title': 'Это главная страница проекта Yatube'
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.group.all()[:POST_OBJ]
    post_list = Post.objects.all()
    page_obj = paginate_posts(request, post_list)
    context = {
        'page_obj': page_obj,
        'group': group,
        'posts': posts,
        'title': group.title
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    post_list = user.posts.all()
    page_obj = paginate_posts(request, post_list)
    total_posts = post_list.count()
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user,
                                          author=user).exists()
    context = {
        'author': user,
        'page_obj': page_obj,
        'total_posts': total_posts,
        'title': f'Профайл пользователя {username}',
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author_posts = Post.objects.filter(author=post.author)
    comments = post.comments.all()
    form = CommentForm()
    context = {
        'post': post,
        'total_posts': author_posts.count(),
        'title': f'Пост: {post.text[:30]}',
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile',
                        username=request.user.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post.id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:post_detail', post_id=post.id)
    context = {
        'form': form,
        'is_edit': True,
        'post': post
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    user = request.user
    posts = Post.objects.filter(author__following__user=user).select_related(
        'group').order_by('-created')
    page_obj = paginate_posts(request, posts)
    context = {
        'page_obj': page_obj,
        'title': 'Новые записи от авторов, на которых вы подписаны'
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if user == author:
        return redirect('posts:profile', username=username)
    Follow.objects.get_or_create(user=user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=user, author=author)
    follow.delete()
    return redirect('posts:profile', username=username)
