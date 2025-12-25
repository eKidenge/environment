from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PartnerOrganizationViewSet, PartnershipProjectViewSet,
    PartnershipAgreementViewSet, PartnerContactViewSet,
    PartnershipMeetingViewSet, PartnershipResourceViewSet,
    PartnerEvaluationViewSet, PartnershipOpportunityViewSet
)

router = DefaultRouter()
router.register(r'organizations', PartnerOrganizationViewSet, basename='partnerorganization')
router.register(r'projects', PartnershipProjectViewSet, basename='partnershipproject')
router.register(r'agreements', PartnershipAgreementViewSet, basename='partnershipagreement')
router.register(r'contacts', PartnerContactViewSet, basename='partnercontact')
router.register(r'meetings', PartnershipMeetingViewSet, basename='partnershipmeeting')
router.register(r'resources', PartnershipResourceViewSet, basename='partnershipresource')
router.register(r'evaluations', PartnerEvaluationViewSet, basename='partnerevaluation')
router.register(r'opportunities', PartnershipOpportunityViewSet, basename='partnershipopportunity')

urlpatterns = [
    path('', include(router.urls)),
]