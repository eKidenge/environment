from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProgramCategoryViewSet, ProgramViewSet,
    ProgramApplicationViewSet, ProgramParticipantViewSet,
    ProgramEventViewSet
)

router = DefaultRouter()
router.register(r'categories', ProgramCategoryViewSet, basename='programcategory')
router.register(r'programs', ProgramViewSet, basename='program')
router.register(r'applications', ProgramApplicationViewSet, basename='programapplication')
router.register(r'participants', ProgramParticipantViewSet, basename='programparticipant')
router.register(r'events', ProgramEventViewSet, basename='programevent')

urlpatterns = [
    path('', include(router.urls)),
    # If you need a simple list view for templates (not API), add this:
    path('list/', ProgramViewSet.as_view({'get': 'list'}), name='program-list'),
    
    # For events list view accessible via template:
    path('events/list/', ProgramEventViewSet.as_view({'get': 'list'}), name='event-list'),
]

app_name = 'programs'