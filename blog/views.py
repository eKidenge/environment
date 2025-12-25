"""
Template Views for Blog - Simple views that render templates
"""
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Count, Q, Sum, F
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import timedelta
from django.conf import settings
from django.views.decorators.http import require_POST

from .models import (
    BlogCategory, BlogTag, BlogPost, BlogComment,
    BlogLike, BlogView, BlogSeries
)


def blog_list(request):
    """Main blog list view"""
    # Get filter parameters
    category_slug = request.GET.get('category')
    tag_slug = request.GET.get('tag')
    search_query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', '-published_at')
    
    # Base queryset
    posts = BlogPost.objects.filter(
        status='published',
        is_published=True
    ).select_related('author', 'category').prefetch_related('tags')
    
    # Apply filters
    if category_slug:
        category = get_object_or_404(BlogCategory, slug=category_slug, is_active=True)
        posts = posts.filter(category=category)
    
    if tag_slug:
        tag = get_object_or_404(BlogTag, slug=tag_slug)
        posts = posts.filter(tags=tag)
    
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) |
            Q(excerpt__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(tags__name__icontains=search_query)
        ).distinct()
    
    # Apply sorting
    if sort_by in ['published_at', '-published_at', 'views', '-views', 'likes', '-likes']:
        posts = posts.order_by(sort_by)
    else:
        posts = posts.order_by('-published_at')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(posts, getattr(settings, 'BLOG_POSTS_PER_PAGE', 12))
    
    try:
        posts_page = paginator.page(page)
    except PageNotAnInteger:
        posts_page = paginator.page(1)
    except EmptyPage:
        posts_page = paginator.page(paginator.num_pages)
    
    # Get categories with post counts
    categories = BlogCategory.objects.filter(is_active=True).annotate(
        post_count=Count('posts', filter=Q(posts__status='published', posts__is_published=True))
    ).filter(post_count__gt=0).order_by('-post_count')
    
    # Get featured posts
    featured_posts = BlogPost.objects.filter(
        is_featured=True,
        status='published',
        is_published=True
    ).select_related('author', 'category').order_by('-published_at')[:4]
    
    # Get popular posts (last 30 days)
    month_ago = timezone.now() - timedelta(days=30)
    popular_posts = BlogPost.objects.filter(
        status='published',
        is_published=True,
        published_at__gte=month_ago
    ).order_by('-views')[:5]
    
    # Get all tags with counts
    tags = BlogTag.objects.annotate(
        post_count=Count('blog_posts', filter=Q(blog_posts__status='published', blog_posts__is_published=True))
    ).filter(post_count__gt=0).order_by('-post_count')[:20]
    
    context = {
        'posts': posts_page,
        'categories': categories,
        'featured_posts': featured_posts,
        'popular_posts': popular_posts,
        'tags': tags,
        'search_query': search_query,
        'current_category': category_slug,
        'current_tag': tag_slug,
        'sort_by': sort_by,
        'page_obj': posts_page,
        'paginator': paginator,
    }
    
    return render(request, 'blog/blog_list.html', context)


def blog_detail(request, slug):
    """Blog post detail view"""
    post = get_object_or_404(
        BlogPost.objects.select_related('author', 'category').prefetch_related('tags'),
        slug=slug,
        status='published',
        is_published=True
    )
    
    # Increment view count
    post.views = F('views') + 1
    post.save(update_fields=['views'])
    post.refresh_from_db()
    
    # Get related posts
    related_posts = BlogPost.objects.filter(
        status='published',
        is_published=True,
        tags__in=post.tags.all()
    ).exclude(id=post.id).distinct().order_by('-published_at')[:3]
    
    # Get comments
    comments = post.comments.filter(status='approved').select_related('author').order_by('created_at')
    
    # Check if user liked the post
    user_liked = False
    if request.user.is_authenticated:
        user_liked = BlogLike.objects.filter(post=post, user=request.user).exists()
    
    context = {
        'post': post,
        'related_posts': related_posts,
        'comments': comments,
        'user_liked': user_liked,
    }
    
    return render(request, 'blog/blog_detail.html', context)


def category_detail(request, slug):
    """Category detail view"""
    category = get_object_or_404(BlogCategory, slug=slug, is_active=True)
    
    posts = BlogPost.objects.filter(
        category=category,
        status='published',
        is_published=True
    ).select_related('author', 'category').prefetch_related('tags')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(posts, getattr(settings, 'BLOG_POSTS_PER_PAGE', 12))
    
    try:
        posts_page = paginator.page(page)
    except PageNotAnInteger:
        posts_page = paginator.page(1)
    except EmptyPage:
        posts_page = paginator.page(paginator.num_pages)
    
    context = {
        'category': category,
        'posts': posts_page,
        'page_obj': posts_page,
        'paginator': paginator,
    }
    
    return render(request, 'blog/category_detail.html', context)


def tag_detail(request, slug):
    """Tag detail view"""
    tag = get_object_or_404(BlogTag, slug=slug)
    
    posts = tag.blog_posts.filter(
        status='published',
        is_published=True
    ).select_related('author', 'category').prefetch_related('tags')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(posts, getattr(settings, 'BLOG_POSTS_PER_PAGE', 12))
    
    try:
        posts_page = paginator.page(page)
    except PageNotAnInteger:
        posts_page = paginator.page(1)
    except EmptyPage:
        posts_page = paginator.page(paginator.num_pages)
    
    context = {
        'tag': tag,
        'posts': posts_page,
        'page_obj': posts_page,
        'paginator': paginator,
    }
    
    return render(request, 'blog/tag_detail.html', context)


def series_detail(request, slug):
    """Series detail view"""
    series = get_object_or_404(BlogSeries, slug=slug, is_active=True)
    
    posts = series.posts.filter(
        status='published',
        is_published=True
    ).select_related('author', 'category').prefetch_related('tags').order_by('created_at')
    
    context = {
        'series': series,
        'posts': posts,
    }
    
    return render(request, 'blog/series_detail.html', context)


def blog_search(request):
    """Search view"""
    query = request.GET.get('q', '')
    
    if query:
        posts = BlogPost.objects.filter(
            Q(title__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(content__icontains=query) |
            Q(tags__name__icontains=query),
            status='published',
            is_published=True
        ).select_related('author', 'category').prefetch_related('tags').distinct().order_by('-published_at')
    else:
        posts = BlogPost.objects.none()
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(posts, getattr(settings, 'BLOG_POSTS_PER_PAGE', 12))
    
    try:
        posts_page = paginator.page(page)
    except PageNotAnInteger:
        posts_page = paginator.page(1)
    except EmptyPage:
        posts_page = paginator.page(paginator.num_pages)
    
    context = {
        'query': query,
        'posts': posts_page,
        'page_obj': posts_page,
        'paginator': paginator,
        'results_count': posts.count(),
    }
    
    return render(request, 'blog/search_results.html', context)


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@require_POST
def api_like_post(request, post_id):
    """API endpoint to like/unlike a post"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        post = BlogPost.objects.get(id=post_id)
    except BlogPost.DoesNotExist:
        return JsonResponse({'error': 'Post not found'}, status=404)
    
    # Check if already liked
    existing_like = BlogLike.objects.filter(post=post, user=request.user).first()
    
    if existing_like:
        # Unlike
        existing_like.delete()
        post.likes = max(0, post.likes - 1)
        post.save(update_fields=['likes'])
        return JsonResponse({'status': 'unliked', 'likes': post.likes})
    else:
        # Like
        BlogLike.objects.create(
            post=post,
            user=request.user,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        post.likes += 1
        post.save(update_fields=['likes'])
        return JsonResponse({'status': 'liked', 'likes': post.likes})