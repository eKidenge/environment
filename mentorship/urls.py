from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MentorshipProgramViewSet, MentorshipApplicationViewSet,
    MentorshipMatchViewSet, MentorshipSessionViewSet,
    MentorshipResourceViewSet, MentorshipFeedbackViewSet,
    MentorshipGoalViewSet
)

router = DefaultRouter()
router.register(r'programs', MentorshipProgramViewSet, basename='mentorshipprogram')
router.register(r'applications', MentorshipApplicationViewSet, basename='mentorshipapplication')
router.register(r'matches', MentorshipMatchViewSet, basename='mentorshipmatch')
router.register(r'sessions', MentorshipSessionViewSet, basename='mentorshipsession')
router.register(r'resources', MentorshipResourceViewSet, basename='mentorshipresource')
router.register(r'feedback', MentorshipFeedbackViewSet, basename='mentorshipfeedback')
router.register(r'goals', MentorshipGoalViewSet, basename='mentorshipgoal')

urlpatterns = [
    path('', include(router.urls)),
]