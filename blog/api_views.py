"""
API Views for Blog - Separate from template views
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings

from .models import (
    BlogCategory, BlogTag, BlogPost, BlogComment,
    BlogLike, BlogView, BlogSeries
)
from .serializers import (
    BlogCategorySerializer, BlogTagSerializer, BlogPostSerializer,
    BlogPostDetailSerializer, BlogCommentSerializer, BlogCommentCreateSerializer,
    BlogLikeSerializer, BlogViewSerializer, BlogSeriesSerializer,
    PublicBlogCategorySerializer, PublicBlogTagSerializer,
    PublicBlogPostSerializer, PublicBlogCommentSerializer
)


class BlogCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for blog categories
    """
    queryset = BlogCategory.objects.filter(is_active=True)
    serializer_class = BlogCategorySerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return PublicBlogCategorySerializer
        return BlogCategorySerializer
    
    @action(detail=True, methods=['get'])
    def posts(self, request, slug=None):
        """Get posts in this category"""
        category = self.get_object()
        posts = BlogPost.objects.filter(
            category=category,
            status='published',
            is_published=True
        ).order_by('-published_at', '-created_at')
        
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = PublicBlogPostSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = PublicBlogPostSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)


class BlogTagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for blog tags
    """
    queryset = BlogTag.objects.all()
    serializer_class = BlogTagSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return PublicBlogTagSerializer
        return BlogTagSerializer
    
    @action(detail=True, methods=['get'])
    def posts(self, request, slug=None):
        """Get posts with this tag"""
        tag = self.get_object()
        posts = tag.blog_posts.filter(
            status='published',
            is_published=True
        ).order_by('-published_at')
        
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = PublicBlogPostSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = PublicBlogPostSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)


class BlogPostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for blog posts
    """
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostSerializer
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_featured', 'author']
    search_fields = ['title', 'excerpt', 'content', 'tags__name']
    ordering_fields = ['published_at', 'created_at', 'views', 'likes']
    ordering = ['-published_at', '-created_at']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BlogPostDetailSerializer
        elif self.action in ['list']:
            return PublicBlogPostSerializer
        return BlogPostSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ['list', 'retrieve']:
            # Only show published posts that aren't scheduled for future
            queryset = queryset.filter(
                status='published',
                is_published=True
            ).filter(
                Q(scheduled_at__isnull=True) | Q(scheduled_at__lte=timezone.now())
            )
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve post and increment view count"""
        instance = self.get_object()
        
        # Increment view count
        instance.views += 1
        instance.save(update_fields=['views'])
        
        # Record detailed view for analytics
        if request.user.is_authenticated:
            BlogView.objects.create(
                post=instance,
                user=request.user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                session_id=request.session.session_key or 'anonymous',
                referrer=request.META.get('HTTP_REFERER', '')
            )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def like(self, request, slug=None):
        """Like or unlike a blog post"""
        post = self.get_object()
        user = request.user
        
        if not user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if already liked
        existing_like = BlogLike.objects.filter(post=post, user=user).first()
        
        if existing_like:
            # Unlike: delete the like
            existing_like.delete()
            post.likes = max(0, post.likes - 1)
            post.save(update_fields=['likes'])
            return Response({'status': 'Post unliked', 'liked': False})
        else:
            # Like: create new like
            BlogLike.objects.create(
                post=post,
                user=user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            post.likes += 1
            post.save(update_fields=['likes'])
            return Response({'status': 'Post liked', 'liked': True})
    
    @action(detail=True, methods=['get'])
    def comments(self, request, slug=None):
        """Get comments for this post"""
        post = self.get_object()
        comments = post.comments.filter(status='approved').order_by('created_at')
        
        page = self.paginate_queryset(comments)
        if page is not None:
            serializer = PublicBlogCommentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = PublicBlogCommentSerializer(comments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured posts"""
        queryset = self.get_queryset().filter(is_featured=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent posts"""
        days = int(request.query_params.get('days', 30))
        cutoff_date = timezone.now() - timedelta(days=days)
        
        queryset = self.get_queryset().filter(
            published_at__gte=cutoff_date
        ).order_by('-published_at')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get popular posts (by views)"""
        days = int(request.query_params.get('days', 30))
        cutoff_date = timezone.now() - timedelta(days=days)
        
        queryset = self.get_queryset().filter(
            published_at__gte=cutoff_date
        ).order_by('-views')[:10]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_author(self, request):
        """Get posts by specific author"""
        author_id = request.query_params.get('author_id')
        if not author_id:
            return Response(
                {'error': 'author_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(author_id=author_id)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def archive(self, request):
        """Get archive by month"""
        archive = BlogPost.objects.filter(
            status='published',
            is_published=True
        ).extra(
            select={'year': 'EXTRACT(YEAR FROM published_at)',
                   'month': 'EXTRACT(MONTH FROM published_at)'}
        ).values('year', 'month').annotate(
            count=Count('id')
        ).order_by('-year', '-month')
        
        return Response(archive)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class BlogCommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for blog comments
    """
    serializer_class = BlogCommentSerializer
    permission_classes = [AllowAny]  # Allow anonymous comments
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['post', 'status']
    ordering_fields = ['created_at']
    ordering = ['created_at']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return BlogComment.objects.all()
        return BlogComment.objects.filter(status='approved')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BlogCommentCreateSerializer
        return BlogCommentSerializer
    
    def get_permissions(self):
        if self.action in ['create']:
            # Allow anyone to create comments
            permission_classes = [AllowAny]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Only allow staff or comment owner to modify
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        comment = serializer.save()
        
        # If user is authenticated, link to user account
        if self.request.user.is_authenticated:
            comment.author = self.request.user
        
        # Set IP address and user agent
        comment.ip_address = self.get_client_ip(self.request)
        comment.user_agent = self.request.META.get('HTTP_USER_AGENT', '')
        
        # Auto-approve comments from authenticated users
        if self.request.user.is_authenticated and self.request.user.is_active:
            comment.status = 'approved'
            comment.approved_at = timezone.now()
        
        comment.save()
        
        # Send notification to post author
        self.send_comment_notification(comment)
    
    def send_comment_notification(self, comment):
        """Send email notification about new comment"""
        post_author = comment.post.author
        
        if post_author.email:
            subject = f'New Comment on "{comment.post.title}"'
            
            if comment.author:
                author_name = comment.author.get_full_name() or comment.author.username
            else:
                author_name = comment.guest_name or 'Anonymous'
            
            message = f"""
            New comment on your post: {comment.post.title}
            
            Comment by: {author_name}
            Content: {comment.content[:200]}...
            
            To moderate this comment, please visit the admin panel.
            
            Comment status: {comment.get_status_display()}
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[post_author.email],
                fail_silently=False,
            )
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class BlogSeriesViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for blog series
    """
    queryset = BlogSeries.objects.filter(is_active=True)
    serializer_class = BlogSeriesSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    
    @action(detail=True, methods=['get'])
    def posts(self, request, slug=None):
        """Get posts in this series"""
        series = self.get_object()
        posts = series.posts.filter(
            status='published',
            is_published=True
        ).order_by('created_at')
        
        serializer = PublicBlogPostSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)