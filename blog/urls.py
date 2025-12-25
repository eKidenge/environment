from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views  # Import from api_views, not views
from . import views  # Template views

# API Router
api_router = DefaultRouter()
api_router.register(r'categories', api_views.BlogCategoryViewSet, basename='category')
api_router.register(r'tags', api_views.BlogTagViewSet, basename='tag')
api_router.register(r'posts', api_views.BlogPostViewSet, basename='post')
api_router.register(r'comments', api_views.BlogCommentViewSet, basename='comment')
api_router.register(r'series', api_views.BlogSeriesViewSet, basename='series')

urlpatterns = [
    # Template URLs (render HTML pages)
    path('', views.blog_list, name='list'),
    path('search/', views.blog_search, name='search'),
    
    # Category URLs
    path('categories/<slug:slug>/', views.category_detail, name='category_detail'),
    
    # Tag URLs
    path('tags/<slug:slug>/', views.tag_detail, name='tag_detail'),
    
    # Series URLs
    path('series/<slug:slug>/', views.series_detail, name='series_detail'),
    
    # Post URLs
    path('<slug:slug>/', views.blog_detail, name='detail'),
    
    # API endpoints for AJAX (JSON responses)
    path('api/posts/<int:post_id>/like/', views.api_like_post, name='api_like_post'),
    
    # REST API endpoints (DRF viewsets)
    path('api/v1/', include(api_router.urls)),
]

# If you want a separate API app, you can also do this:
# app_name = 'blog'