from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ResearchCategoryViewSet, ResearchPublicationViewSet,
    ResearchDatasetViewSet, ResearchProjectViewSet,
    ResearchToolViewSet, LiteratureReviewViewSet
)

router = DefaultRouter()
router.register(r'categories', ResearchCategoryViewSet, basename='researchcategory')
router.register(r'publications', ResearchPublicationViewSet, basename='publication')
router.register(r'datasets', ResearchDatasetViewSet, basename='dataset')
router.register(r'projects', ResearchProjectViewSet, basename='project')
router.register(r'tools', ResearchToolViewSet, basename='tool')
router.register(r'reviews', LiteratureReviewViewSet, basename='literaturereview')

urlpatterns = [
    path('', include(router.urls)),
]