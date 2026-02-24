from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Category, Post, Comment, Like


def forum_home(request):
    categories = Category.objects.all()
    recent_posts = Post.objects.all().order_by('-created_at')[:10]
    return render(request, 'forum/forum_home.html', {
        'categories': categories,
        'recent_posts': recent_posts
    })


def category_posts(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    posts = category.posts.all().order_by('-is_pinned', '-created_at')
    return render(request, 'forum/category_posts.html', {
        'category': category,
        'posts': posts
    })


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.views += 1
    post.save()
    
    comments = post.comments.filter(parent=None).order_by('created_at')
    return render(request, 'forum/post_detail.html', {
        'post': post,
        'comments': comments
    })


@login_required
def create_post(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        category_id = request.POST.get('category')
        
        category = get_object_or_404(Category, id=category_id)
        post = Post.objects.create(
            title=title,
            content=content,
            author=request.user,
            category=category
        )
        messages.success(request, 'Post created successfully!')
        return redirect('forum:post_detail', post_id=post.id)
    
    categories = Category.objects.all()
    return render(request, 'forum/create_post.html', {'categories': categories})


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    
    if request.method == 'POST':
        post.title = request.POST.get('title')
        post.content = request.POST.get('content')
        post.save()
        messages.success(request, 'Post updated successfully!')
        return redirect('forum:post_detail', post_id=post.id)
    
    return render(request, 'forum/edit_post.html', {'post': post})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        parent_id = request.POST.get('parent_id')
        
        comment = Comment.objects.create(
            post=post,
            author=request.user,
            content=content
        )
        
        if parent_id:
            parent = get_object_or_404(Comment, id=parent_id)
            comment.parent = parent
            comment.save()
        
        messages.success(request, 'Comment added successfully!')
    
    return redirect('forum:post_detail', post_id=post.id)


@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(
        user=request.user,
        post=post
    )
    
    if not created:
        like.delete()
        messages.success(request, 'Post unliked!')
    else:
        messages.success(request, 'Post liked!')
    
    return redirect('forum:post_detail', post_id=post.id)
