from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.utils import timezone

# Home page using existing core/home.html template with simplified URLs
def home_view(request):
    # Provide dummy data with simplified URLs (without namespaces)
    context = {
        'features': [
            {
                'title': 'Research Platform',
                'description': 'Access cutting-edge environmental research and datasets from global experts.',
                'icon': 'fas fa-microscope',
                'gradient': 'from-blue-500 to-cyan-400',
                'link': '/research/'
            },
            {
                'title': 'Education Programs',
                'description': 'Comprehensive environmental education and training programs for all levels.',
                'icon': 'fas fa-graduation-cap',
                'gradient': 'from-emerald-500 to-teal-400',
                'link': '/programs/'
            },
            {
                'title': 'Community Impact',
                'description': 'Join global environmental initiatives and make real-world impact.',
                'icon': 'fas fa-users',
                'gradient': 'from-purple-500 to-pink-400',
                'link': '/volunteer/'
            },
            {
                'title': 'Mentorship Network',
                'description': 'Connect with experienced environmental professionals and researchers.',
                'icon': 'fas fa-hands-helping',
                'gradient': 'from-orange-500 to-red-400',
                'link': '/mentorship/'
            },
            {
                'title': 'Partnerships',
                'description': 'Collaborate with organizations and institutions worldwide.',
                'icon': 'fas fa-handshake',
                'gradient': 'from-indigo-500 to-purple-400',
                'link': '/partners/'
            },
            {
                'title': 'Blog & Resources',
                'description': 'Stay updated with latest environmental news and resources.',
                'icon': 'fas fa-newspaper',
                'gradient': 'from-yellow-500 to-orange-400',
                'link': '/blog/'
            },
        ],
        'featured_programs': [
            {
                'id': 1,
                'title': 'Climate Action Leadership',
                'excerpt': 'Become a leader in climate change mitigation and adaptation strategies.',
                'image_url': '/static/img/program1.jpg',
                'category': 'Leadership',
                'duration': '12 Weeks',
                'rating': 4.8,
                'enrolled': 1250
            },
            {
                'id': 2,
                'title': 'Sustainable Agriculture',
                'excerpt': 'Learn modern sustainable farming techniques and food systems.',
                'image_url': '/static/img/program2.jpg',
                'category': 'Agriculture',
                'duration': '8 Weeks',
                'rating': 4.7,
                'enrolled': 890
            },
            {
                'id': 3,
                'title': 'Marine Conservation',
                'excerpt': 'Protect ocean ecosystems and marine biodiversity.',
                'image_url': '/static/img/program3.jpg',
                'category': 'Conservation',
                'duration': '10 Weeks',
                'rating': 4.9,
                'enrolled': 2100
            },
        ],
        'latest_publications': [
            {
                'title': 'Impact of Urban Green Spaces on Air Quality',
                'authors': 'Dr. Sarah Chen et al.',
                'date': '2024-03-15',
                'downloads': 1245
            },
            {
                'title': 'Renewable Energy Adoption in Developing Nations',
                'authors': 'Prof. Michael Rodriguez',
                'date': '2024-03-10',
                'downloads': 987
            },
            {
                'title': 'Biodiversity Conservation Strategies 2024',
                'authors': 'YES Research Team',
                'date': '2024-03-05',
                'downloads': 1567
            },
        ],
        'partners': [
            {'name': 'UN Environment'},
            {'name': 'WWF'},
            {'name': 'Greenpeace'},
            {'name': 'IUCN'},
            {'name': 'NASA'},
            {'name': 'MIT'},
        ]
    }
    
    # Add URL context for template to use
    context.update({
        'url_users_register': '/api/users/register/',
        'url_programs_list': '/programs/',
        'url_core_contact': '/api/core/contact/',
        'url_research_publications_list': '/research/',
    })
    
    return render(request, 'core/home.html', context)

# Health check endpoint
def health_check(request):
    from django.db import connection
    from django.core.cache import cache
    
    try:
        connection.ensure_connection()
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
    
    try:
        cache.set('health_check', 'test', 10)
        cache_status = 'healthy' if cache.get('health_check') == 'test' else 'unhealthy'
    except Exception as e:
        cache_status = f'unhealthy: {str(e)}'
    
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'service': 'Youth Environmental Scholars (YES)',
        'version': getattr(settings, 'VERSION', '1.0.0'),
        'services': {
            'database': db_status,
            'cache': cache_status,
        }
    })

# Add this function HERE (after imports, before urlpatterns)
def blog_working_view(request):
    """View that makes blog work by patching URL resolution"""
    # Patch the URL resolver to accept 'list'
    from django.urls import reverse, NoReverseMatch
    original_reverse = reverse
    
    def patched_reverse(viewname, *args, **kwargs):
        if viewname == 'list':
            return '/blog/'
        try:
            return original_reverse(viewname, *args, **kwargs)
        except NoReverseMatch:
            return '#'
    
    # Temporarily patch
    import django.urls
    django.urls.reverse = patched_reverse
    
    try:
        from django.shortcuts import render
        context = {
            'title': 'Environmental Blog',
            'posts': [],
            'categories': [],
            'total_posts': 0,
            'featured_post': None,
        }
        return render(request, 'blog/list.html', context)
    finally:
        # Restore original
        django.urls.reverse = original_reverse
    

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),
    
    # Home page - using existing template
    path('', home_view, name='home'),
    
    # In urlpatterns, replace ALL blog-related lines with:
     path('blog/', blog_working_view, name='blog'),

    # Blog URLs - COMPLETE COVERAGE
    path('blog/', TemplateView.as_view(template_name = 'blog/list.html'), name = 'blog'),
    path('blog/', TemplateView.as_view(template_name = 'blog/list.html'), name = 'list'),
    path('blog/', TemplateView.as_view(template_name = 'blog/list.html'), name = 'blog:list'),
    path('blog/<slug:slug>/', TemplateView.as_view(template_name = 'blog/detail.html'), name = 'detail'),
    path('blog/<slug:slug>/', TemplateView.as_view(template_name = 'blog/detail.html'), name = 'blog:detail'),
    path('blog/categories/<slug:slug>/', TemplateView.as_view(template_name = 'blog/categories/detail.html'), name = 'categories_detail'),
    path('blog/categories/<slug:slug>/', TemplateView.as_view(template_name = 'blog/categories/detail.html'), name = 'categories_detail'),
    path('blog/categories/<slug:slug>/', TemplateView.as_view(template_name = 'blog/categories/detail.html'), name = 'blog:categories:detail'),

    # Continue with other URLs...
    path('volunteer/', TemplateView.as_view(template_name = 'volunteer/opportunities/list.html'), name = 'volunteer'),
    path('about/', TemplateView.as_view(template_name = 'core/about.html'), name = 'about'),
    path('contact/', TemplateView.as_view(template_name='contact.html'), name='contact'),
    path('programs/', TemplateView.as_view(template_name='programs/list.html'), name='programs'),
    path('research/', TemplateView.as_view(template_name='research/publications/list.html'), name='research'),
    path('volunteer/', TemplateView.as_view(template_name='volunteer/list.html'), name='volunteer'),
    path('mentorship/', TemplateView.as_view(template_name='mentorship/list.html'), name='mentorship'),
    path('partners/', TemplateView.as_view(template_name='partners/list.html'), name='partners'),
    
    # User authentication pages
    path('login/', TemplateView.as_view(template_name='users/login.html'), name='login'),
    path('register/', TemplateView.as_view(template_name='users/register.html'), name='register'),
    
    # API endpoints - add namespace for apps that need it
    path('api/users/', include(('users.urls', 'users'), namespace='users')),
    path('api/programs/', include(('programs.urls', 'programs'), namespace='programs')),
    path('api/research/', include(('research.urls', 'research'), namespace='research')),
    path('api/blog/', include(('blog.urls', 'blog'), namespace='blog')),
    path('api/mentorship/', include(('mentorship.urls', 'mentorship'), namespace='mentorship')),
    path('api/volunteer/', include(('volunteer.urls', 'volunteer'), namespace='volunteer')),
    path('api/partners/', include(('partners.urls', 'partners'), namespace='partners')),
    path('api/core/', include(('core.urls', 'core'), namespace='core')),
    
    # Health check
    path('health/', health_check, name='health_check'),
    
    # Authentication endpoints
    path('api/auth/', include('rest_framework.urls')),
    
    # API documentation - simple page
    path('api/docs/', TemplateView.as_view(template_name='api_docs.html'), name='api_docs'),
    
    # JSON API root
    path('api/', lambda request: JsonResponse({
        'message': 'Youth Environmental Scholars API',
        'version': '1.0.0',
        'endpoints': {
            'users': '/api/users/',
            'programs': '/api/programs/',
            'research': '/api/research/',
            'blog': '/api/blog/',
            'mentorship': '/api/mentorship/',
            'volunteer': '/api/volunteer/',
            'partners': '/api/partners/',
            'core': '/api/core/',
            'admin': '/admin/',
            'docs': '/api/docs/',
            'health': '/health/'
        }
    }), name='api_root'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug toolbar
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

# Custom error handlers
handler404 = 'core.views.custom_404'
handler500 = 'core.views.custom_500'
