from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SiteConfigurationViewSet, TeamMemberViewSet,
    PartnerOrganizationViewSet, ImpactMetricViewSet,
    FAQViewSet, SitePageViewSet, NewsletterSubscriptionViewSet,
    health_check, contact_form, contact_page  # ← ADD THIS IMPORT
)

router = DefaultRouter()
router.register(r'site-config', SiteConfigurationViewSet, basename='siteconfig')
router.register(r'team-members', TeamMemberViewSet, basename='teammember')
router.register(r'partners', PartnerOrganizationViewSet, basename='partner')
router.register(r'metrics', ImpactMetricViewSet, basename='metric')
router.register(r'faqs', FAQViewSet, basename='faq')
router.register(r'pages', SitePageViewSet, basename='page')
router.register(r'newsletter', NewsletterSubscriptionViewSet, basename='newsletter')

urlpatterns = [
    path('', include(router.urls)),
    path('health/', health_check, name='health_check'),
    path('contact/', contact_form, name='contact'),
    path('home/', contact_form, name='home'),  # Add this line
    path('contact/', contact_page, name='contact_page'),       # ← HTML page
    path('api/contact/', contact_form, name='contact_api'),    # ← API endpoint
]

app_name = 'core'
