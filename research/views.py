from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Avg, Sum
from django.utils import timezone
from datetime import timedelta
import logging

from .models import (
    ResearchCategory, ResearchPublication, ResearchDataset,
    ResearchProject, ResearchTool, LiteratureReview
)
from .serializers import (
    ResearchCategorySerializer, ResearchPublicationSerializer,
    ResearchPublicationDetailSerializer, ResearchDatasetSerializer,
    ResearchProjectSerializer, ResearchToolSerializer,
    LiteratureReviewSerializer, PublicResearchCategorySerializer,
    PublicResearchPublicationSerializer, PublicResearchDatasetSerializer,
    PublicResearchProjectSerializer, PublicResearchToolSerializer
)

logger = logging.getLogger(__name__)


class ResearchCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for research categories
    """
    queryset = ResearchCategory.objects.filter(is_active=True)
    serializer_class = ResearchCategorySerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return PublicResearchCategorySerializer
        return ResearchCategorySerializer
    
    @action(detail=True, methods=['get'])
    def publications(self, request, slug=None):
        """Get publications in this category"""
        category = self.get_object()
        publications = ResearchPublication.objects.filter(
            category=category,
            is_published=True
        ).order_by('-publication_date')
        
        page = self.paginate_queryset(publications)
        if page is not None:
            serializer = PublicResearchPublicationSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = PublicResearchPublicationSerializer(publications, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, slug=None):
        """Get statistics for this category"""
        category = self.get_object()
        stats = {
            'total_publications': category.publications.filter(is_published=True).count(),
            'publications_by_type': category.publications.filter(is_published=True)
                .values('publication_type')
                .annotate(count=Count('id'))
                .order_by('-count'),
            'total_citations': category.publications.filter(is_published=True)
                .aggregate(total=Sum('citation_count'))['total'] or 0,
            'total_downloads': category.publications.filter(is_published=True)
                .aggregate(total=Sum('downloads'))['total'] or 0,
            'peer_reviewed_count': category.publications.filter(
                is_published=True,
                peer_review_status='peer_reviewed'
            ).count(),
        }
        return Response(stats)


class ResearchPublicationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for research publications
    """
    queryset = ResearchPublication.objects.all()
    serializer_class = ResearchPublicationSerializer
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['publication_type', 'category', 'peer_review_status', 'access_rights', 'is_featured']
    search_fields = ['title', 'abstract', 'authors', 'keywords', 'doi', 'journal_name']
    ordering_fields = ['publication_date', 'citation_count', 'views', 'downloads']
    ordering = ['-publication_date']
    
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
            return ResearchPublicationDetailSerializer
        elif self.action in ['list']:
            return PublicResearchPublicationSerializer
        return ResearchPublicationSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ['list', 'retrieve']:
            queryset = queryset.filter(is_published=True)
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve publication and increment view count"""
        instance = self.get_object()
        instance.views += 1
        instance.save(update_fields=['views'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def download(self, request, slug=None):
        """Record a download and increment download count"""
        publication = self.get_object()
        publication.downloads += 1
        publication.save(update_fields=['downloads'])
        
        logger.info(f"Publication {publication.title} downloaded by {request.user}")
        return Response({'status': 'Download recorded'})
    
    @action(detail=True, methods=['get'])
    def citation(self, request, slug=None):
        """Get citation in different formats"""
        publication = self.get_object()
        style = request.query_params.get('style', 'apa')
        
        citation = publication.generate_citation(style)
        return Response({
            'citation': citation,
            'style': style,
            'formats': ['apa', 'mla', 'chicago', 'harvard']
        })
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent publications"""
        days = int(request.query_params.get('days', 30))
        cutoff_date = timezone.now() - timedelta(days=days)
        
        queryset = self.get_queryset().filter(
            publication_date__gte=cutoff_date
        ).order_by('-publication_date')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def top_cited(self, request):
        """Get most cited publications"""
        queryset = self.get_queryset().order_by('-citation_count')[:50]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_year(self, request):
        """Get publications grouped by year"""
        years = ResearchPublication.objects.filter(is_published=True).dates(
            'publication_date', 'year', order='DESC'
        )
        
        result = []
        for year in years:
            count = ResearchPublication.objects.filter(
                is_published=True,
                publication_date__year=year.year
            ).count()
            
            result.append({
                'year': year.year,
                'count': count,
                'publications': PublicResearchPublicationSerializer(
                    ResearchPublication.objects.filter(
                        is_published=True,
                        publication_date__year=year.year
                    )[:5],
                    many=True,
                    context={'request': request}
                ).data
            })
        
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get publication statistics"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        stats = {
            'total_publications': ResearchPublication.objects.count(),
            'published_publications': ResearchPublication.objects.filter(is_published=True).count(),
            'publications_by_type': ResearchPublication.objects.filter(is_published=True)
                .values('publication_type')
                .annotate(count=Count('id'))
                .order_by('-count'),
            'publications_by_year': ResearchPublication.objects.filter(is_published=True)
                .extra(select={'year': 'EXTRACT(YEAR FROM publication_date)'})
                .values('year')
                .annotate(count=Count('id'))
                .order_by('-year'),
            'total_citations': ResearchPublication.objects.filter(is_published=True)
                .aggregate(total=Sum('citation_count'))['total'] or 0,
            'total_downloads': ResearchPublication.objects.filter(is_published=True)
                .aggregate(total=Sum('downloads'))['total'] or 0,
            'total_views': ResearchPublication.objects.filter(is_published=True)
                .aggregate(total=Sum('views'))['total'] or 0,
            'peer_reviewed_count': ResearchPublication.objects.filter(
                is_published=True,
                peer_review_status='peer_reviewed'
            ).count(),
            'open_access_count': ResearchPublication.objects.filter(
                is_published=True,
                access_rights='open_access'
            ).count(),
            'average_citations': ResearchPublication.objects.filter(is_published=True)
                .aggregate(avg=Avg('citation_count'))['avg'] or 0,
        }
        
        return Response(stats)


class ResearchDatasetViewSet(viewsets.ModelViewSet):
    """
    ViewSet for research datasets
    """
    queryset = ResearchDataset.objects.all()
    serializer_class = ResearchDatasetSerializer
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['dataset_type', 'access_type', 'license_type', 'is_verified']
    search_fields = ['title', 'description', 'keywords', 'doi']
    ordering_fields = ['created_at', 'views', 'downloads', 'citations']
    ordering = ['-created_at']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return PublicResearchDatasetSerializer
        return ResearchDatasetSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ['list', 'retrieve']:
            # Check embargo dates
            queryset = queryset.filter(
                Q(access_type='open') |
                Q(access_type='embargoed', embargo_date__lte=timezone.now().date()) |
                Q(access_type='restricted', is_verified=True)
            )
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve dataset and increment view count"""
        instance = self.get_object()
        instance.views += 1
        instance.save(update_fields=['views'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def download(self, request, slug=None):
        """Record a dataset download"""
        dataset = self.get_object()
        
        # Check access
        if dataset.access_type == 'controlled' and not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required to download this dataset'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        dataset.downloads += 1
        dataset.save(update_fields=['downloads'])
        
        logger.info(f"Dataset {dataset.title} downloaded by {request.user}")
        return Response({'status': 'Download recorded'})
    
    @action(detail=False, methods=['get'])
    def formats(self, request):
        """Get available dataset formats"""
        formats = ResearchDataset.objects.values_list('file_formats', flat=True)
        all_formats = set()
        for format_list in formats:
            if format_list:
                all_formats.update(format_list)
        
        return Response(sorted(all_formats))


class ResearchProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for research projects
    """
    queryset = ResearchProject.objects.all()
    serializer_class = ResearchProjectSerializer
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'is_featured', 'is_public']
    search_fields = ['title', 'abstract', 'objectives', 'research_questions']
    ordering_fields = ['start_date', 'created_at', 'progress_percentage']
    ordering = ['-created_at']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return PublicResearchProjectSerializer
        return ResearchProjectSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ['list', 'retrieve']:
            queryset = queryset.filter(is_public=True)
        return queryset
    
    @action(detail=True, methods=['get'])
    def publications(self, request, slug=None):
        """Get publications from this project"""
        project = self.get_object()
        publications = project.publications.filter(is_published=True)
        serializer = PublicResearchPublicationSerializer(publications, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def datasets(self, request, slug=None):
        """Get datasets from this project"""
        project = self.get_object()
        datasets = project.datasets.all()
        serializer = PublicResearchDatasetSerializer(datasets, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active research projects"""
        queryset = self.get_queryset().filter(
            status__in=['ongoing', 'planning'],
            is_public=True
        ).order_by('-start_date')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ResearchToolViewSet(viewsets.ModelViewSet):
    """
    ViewSet for research tools
    """
    queryset = ResearchTool.objects.all()
    serializer_class = ResearchToolSerializer
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tool_type', 'license']
    search_fields = ['name', 'description', 'programming_language']
    ordering_fields = ['created_at', 'download_count', 'citation_count']
    ordering = ['-created_at']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return PublicResearchToolSerializer
        return ResearchToolSerializer
    
    @action(detail=True, methods=['post'])
    def download(self, request, slug=None):
        """Record a tool download"""
        tool = self.get_object()
        tool.download_count += 1
        tool.save(update_fields=['download_count'])
        
        logger.info(f"Tool {tool.name} downloaded by {request.user}")
        return Response({'status': 'Download recorded'})


class LiteratureReviewViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for literature reviews
    """
    queryset = LiteratureReview.objects.all()
    serializer_class = LiteratureReviewSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'research_question', 'key_findings', 'recommendations']