from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Sum
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

# Import the PartnerOrganization from partners app
from partners.models import PartnerOrganization

from .models import (
    SiteConfiguration, TeamMember, ImpactMetric,
    FAQ, SitePage, NewsletterSubscription
)
from .serializers import (
    SiteConfigurationSerializer, TeamMemberSerializer,
    PartnerOrganizationSerializer, ImpactMetricSerializer,
    FAQSerializer, SitePageSerializer, NewsletterSubscriptionSerializer,
    PublicSiteConfigurationSerializer, PublicTeamMemberSerializer,
    PublicPartnerOrganizationSerializer, PublicImpactMetricSerializer,
    PublicFAQSerializer, PublicSitePageSerializer,
    NewsletterSubscriptionCreateSerializer
)

logger = logging.getLogger(__name__)

class SiteConfigurationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for site configuration (read-only for most users)
    """
    queryset = SiteConfiguration.objects.all()
    serializer_class = SiteConfigurationSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def public(self, request):
        """
        Get public site configuration
        """
        config = SiteConfiguration.objects.first()
        if config:
            serializer = PublicSiteConfigurationSerializer(config)
            return Response(serializer.data)
        return Response({'error': 'Site configuration not found'}, 
                       status=status.HTTP_404_NOT_FOUND)


class TeamMemberViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing team members
    """
    queryset = TeamMember.objects.filter(is_active=True, show_on_website=True)
    serializer_class = TeamMemberSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'department', 'is_leadership']
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'bio', 'department']
    ordering_fields = ['display_order', 'user__last_name', 'years_with_yes']
    ordering = ['display_order', '-is_leadership', 'user__last_name']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return PublicTeamMemberSerializer
        return TeamMemberSerializer
    
    @action(detail=False, methods=['get'])
    def leadership(self, request):
        """
        Get leadership team members
        """
        queryset = self.get_queryset().filter(is_leadership=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def departments(self, request):
        """
        Get list of departments with member counts
        """
        departments = TeamMember.objects.filter(
            is_active=True, 
            show_on_website=True,
            department__isnull=False
        ).values('department').annotate(
            count=Count('id'),
            leadership_count=Count('id', filter=Q(is_leadership=True))
        ).order_by('department')
        
        return Response(departments)


class PartnerOrganizationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing partner organizations
    """
    queryset = PartnerOrganization.objects.filter(status='active')
    serializer_class = PartnerOrganizationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['partner_type', 'partnership_level', 'country', 'is_featured']
    search_fields = ['name', 'description', 'mission', 'contact_person', 'city']
    ordering_fields = ['name', 'partnership_start_date', 'total_funding']
    ordering = ['-is_featured', '-partnership_start_date', 'name']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return PublicPartnerOrganizationSerializer
        return PartnerOrganizationSerializer
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        Get featured partner organizations
        """
        queryset = self.get_queryset().filter(is_featured=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get partner statistics
        """
        stats = {
            'total_partners': PartnerOrganization.objects.filter(status='active').count(),
            'partners_by_type': PartnerOrganization.objects.filter(status='active')
                .values('partner_type')
                .annotate(count=Count('id'))
                .order_by('-count'),
            'partners_by_country': PartnerOrganization.objects.filter(
                status='active', 
                country__isnull=False
            ).values('country')
                .annotate(count=Count('id'))
                .order_by('-count'),
            'total_funding': PartnerOrganization.objects.filter(status='active')
                .aggregate(total=Sum('total_funding'))['total'] or 0,
            'projects_supported': PartnerOrganization.objects.filter(status='active')
                .aggregate(total=Sum('projects_supported'))['total'] or 0,
        }
        
        return Response(stats)


class ImpactMetricViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing impact metrics
    """
    queryset = ImpactMetric.objects.all()
    serializer_class = ImpactMetricSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['metric_type', 'is_public']
    search_fields = ['name', 'description', 'unit']
    ordering_fields = ['display_order', 'name', 'current_value']
    ordering = ['display_order', 'name']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return PublicImpactMetricSerializer
        return ImpactMetricSerializer
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """
        Get metrics for dashboard display
        """
        metrics = self.get_queryset().filter(is_public=True)
        serializer = self.get_serializer(metrics, many=True)
        
        # Calculate overall impact
        total_impact = {
            'total_metrics': metrics.count(),
            'total_value': sum(float(metric.current_value) for metric in metrics),
            'progress_average': sum(metric.calculate_progress() for metric in metrics) / metrics.count() if metrics.count() > 0 else 0,
        }
        
        return Response({
            'metrics': serializer.data,
            'overall': total_impact
        })
    
    @action(detail=True, methods=['post'])
    def update_value(self, request, pk=None):
        """
        Update metric value with history tracking
        """
        metric = self.get_object()
        new_value = request.data.get('value')
        
        if new_value is None:
            return Response(
                {'error': 'Value is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add to history
        history_entry = {
            'timestamp': timezone.now().isoformat(),
            'value': float(metric.current_value),
            'updated_by': request.user.username if request.user.is_authenticated else 'system'
        }
        
        metric.history.append(history_entry)
        metric.current_value = new_value
        metric.last_updated_by = request.user if request.user.is_authenticated else None
        metric.save()
        
        logger.info(f"Metric {metric.name} updated to {new_value} by {request.user}")
        return Response({'status': 'Metric updated successfully'})


class FAQViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing FAQs
    """
    queryset = FAQ.objects.filter(is_published=True)
    serializer_class = FAQSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_featured']
    search_fields = ['question', 'answer']
    ordering_fields = ['display_order', 'question']
    ordering = ['display_order', 'category', 'question']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return PublicFAQSerializer
        return FAQSerializer
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """
        Get FAQ categories with counts
        """
        categories = FAQ.objects.filter(is_published=True).values(
            'category'
        ).annotate(
            count=Count('id'),
            featured_count=Count('id', filter=Q(is_featured=True))
        ).order_by('category')
        
        return Response(categories)
    
    @action(detail=True, methods=['post'])
    def mark_helpful(self, request, pk=None):
        """
        Mark FAQ as helpful or not helpful
        """
        faq = self.get_object()
        is_helpful = request.data.get('helpful', None)
        
        if is_helpful is None:
            return Response(
                {'error': 'helpful parameter is required (true/false)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if is_helpful:
            faq.helpful_yes += 1
        else:
            faq.helpful_no += 1
        
        faq.save()
        return Response({'status': 'Feedback recorded'})


class SitePageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing site pages
    """
    queryset = SitePage.objects.filter(is_published=True)
    serializer_class = SitePageSerializer
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['page_type', 'show_in_navigation']
    search_fields = ['title', 'slug', 'content', 'excerpt']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return PublicSitePageSerializer
        return SitePageSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a page and increment view count
        """
        instance = self.get_object()
        
        # Check authentication if required
        if instance.require_authentication and not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required to view this page'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Increment view count
        instance.views += 1
        instance.save(update_fields=['views'])
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def navigation(self, request):
        """
        Get pages for navigation menu
        """
        pages = SitePage.objects.filter(
            is_published=True,
            show_in_navigation=True
        ).order_by('navigation_order')
        
        # Build hierarchical structure
        def build_tree(parent=None):
            children = pages.filter(parent=parent)
            result = []
            for child in children:
                node = {
                    'title': child.title,
                    'slug': child.slug,
                    'children': build_tree(child)
                }
                result.append(node)
            return result
        
        navigation_tree = build_tree()
        return Response(navigation_tree)


class NewsletterSubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for newsletter subscriptions
    """
    queryset = NewsletterSubscription.objects.all()
    serializer_class = NewsletterSubscriptionSerializer
    permission_classes = [IsAdminUser]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return NewsletterSubscriptionCreateSerializer
        return NewsletterSubscriptionSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create a new newsletter subscription
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Check if email already exists
            email = serializer.validated_data['email']
            existing = NewsletterSubscription.objects.filter(email=email).first()
            
            if existing:
                if existing.is_active:
                    return Response(
                        {'error': 'Email already subscribed'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    # Reactivate existing subscription
                    existing.is_active = True
                    existing.unsubscribed_at = None
                    existing.save()
                    return Response(
                        NewsletterSubscriptionSerializer(existing).data,
                        status=status.HTTP_200_OK
                    )
            
            # Create new subscription
            subscription = serializer.save(
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Send verification email
            self.send_verification_email(subscription)
            
            return Response(
                NewsletterSubscriptionSerializer(subscription).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def verify(self, request):
        """
        Verify newsletter subscription
        """
        token = request.data.get('token')
        email = request.data.get('email')
        
        if not token or not email:
            return Response(
                {'error': 'Token and email are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            subscription = NewsletterSubscription.objects.get(
                email=email,
                verification_token=token,
                is_verified=False
            )
            subscription.is_verified = True
            subscription.verified_at = timezone.now()
            subscription.save()
            
            return Response({'status': 'Email verified successfully'})
        except NewsletterSubscription.DoesNotExist:
            return Response(
                {'error': 'Invalid verification token or email'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def unsubscribe(self, request):
        """
        Unsubscribe from newsletter
        """
        email = request.data.get('email')
        
        if not email:
            return Response(
                {'error': 'Email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            subscription = NewsletterSubscription.objects.get(email=email, is_active=True)
            subscription.is_active = False
            subscription.unsubscribed_at = timezone.now()
            subscription.save()
            
            return Response({'status': 'Unsubscribed successfully'})
        except NewsletterSubscription.DoesNotExist:
            return Response(
                {'error': 'Email not found or already unsubscribed'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def send_verification_email(self, subscription):
        """
        Send verification email to subscriber
        """
        subject = 'Verify your newsletter subscription - Youth Environmental Scholars'
        verification_url = f"{settings.FRONTEND_URL}/newsletter/verify/{subscription.verification_token}/{subscription.email}"
        
        message = f"""
        Dear {subscription.name or 'Subscriber'},
        
        Thank you for subscribing to the Youth Environmental Scholars newsletter!
        
        Please verify your email address by clicking the link below:
        {verification_url}
        
        If you did not subscribe to our newsletter, please ignore this email.
        
        Best regards,
        The YES Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[subscription.email],
            fail_silently=False,
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for monitoring
    """
    from django.db import connection
    from django.core.cache import cache
    
    # Check database
    try:
        connection.ensure_connection()
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
    
    # Check cache
    try:
        cache.set('health_check', 'test', 10)
        cache_status = 'healthy' if cache.get('health_check') == 'test' else 'unhealthy'
    except Exception as e:
        cache_status = f'unhealthy: {str(e)}'
    
    return Response({
        'status': 'ok',
        'timestamp': timezone.now().isoformat(),
        'services': {
            'database': db_status,
            'cache': cache_status,
        },
        'version': settings.VERSION if hasattr(settings, 'VERSION') else '1.0.0',
    })


# ADDED TO SERVE CONTACT US
@api_view(['POST'])
@permission_classes([AllowAny])
def contact_form(request):
    """
    Handle contact form submissions
    """
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    
    name = request.data.get('name', '').strip()
    email = request.data.get('email', '').strip()
    subject = request.data.get('subject', '').strip()
    message = request.data.get('message', '').strip()
    category = request.data.get('category', 'general')
    
    # Validation
    if not all([name, email, subject, message]):
        return Response(
            {'error': 'All fields are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not email or '@' not in email:
        return Response(
            {'error': 'Valid email is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Save to database (you might want to create a ContactSubmission model)
    # For now, just send email
    
    # Email to admin
    admin_subject = f'Contact Form: {subject}'
    admin_message = f"""
    Name: {name}
    Email: {email}
    Category: {category}
    
    Message:
    {message}
    
    ---
    This message was sent from the contact form on YES website.
    """
    
    try:
        # Get admin email from site configuration
        config = SiteConfiguration.objects.first()
        admin_email = config.contact_email if config else settings.DEFAULT_FROM_EMAIL
        
        send_mail(
            subject=admin_subject,
            message=admin_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            fail_silently=False,
        )
        
        # Auto-reply to user
        user_subject = 'Thank you for contacting Youth Environmental Scholars'
        user_message = f"""
        Dear {name},
        
        Thank you for contacting Youth Environmental Scholars. We have received your message and will get back to you as soon as possible.
        
        Your message:
        {message}
        
        Best regards,
        The YES Team
        """
        
        send_mail(
            subject=user_subject,
            message=user_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        
        logger.info(f"Contact form submitted by {name} ({email})")
        return Response({'status': 'Message sent successfully'})
    
    except Exception as e:
        logger.error(f"Failed to send contact form email: {str(e)}")
        return Response(
            {'error': 'Failed to send message. Please try again later.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# core/views.py
from django.shortcuts import render

# Add this function alongside your API view
def contact_page(request):
    """Render the contact page template."""
    return render(request, 'contact.html', {
        'page_title': 'Contact Us',
        'meta_description': 'Get in touch with Youth Environmental Scholars',
    })
def custom_404(request, exception):
    '''
    Custom 404 error handler
    '''
    from django.shortcuts import render
    return render(request, 'errors/404.html', status=404)

def custom_500(request):
    '''
    Custom 500 error handler  
    '''
    from django.shortcuts import render
    return render(request, 'errors/500.html', status=500)
