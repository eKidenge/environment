from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VolunteerOpportunityViewSet, VolunteerApplicationViewSet,
    VolunteerAssignmentViewSet, VolunteerTimeLogViewSet,
    VolunteerSkillViewSet, VolunteerAwardViewSet, VolunteerEventViewSet
)

router = DefaultRouter()
router.register(r'opportunities', VolunteerOpportunityViewSet, basename='volunteeropportunity')
router.register(r'applications', VolunteerApplicationViewSet, basename='volunteerapplication')
router.register(r'assignments', VolunteerAssignmentViewSet, basename='volunteerassignment')
router.register(r'time-logs', VolunteerTimeLogViewSet, basename='volunteertimelog')
router.register(r'skills', VolunteerSkillViewSet, basename='volunteerskill')
router.register(r'awards', VolunteerAwardViewSet, basename='volunteeraward')
router.register(r'events', VolunteerEventViewSet, basename='volunteerevent')

urlpatterns = [
    path('', include(router.urls)),
]