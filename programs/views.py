from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Avg, Sum
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
import logging

from .models import (
    ProgramCategory, Program, ProgramApplication,
    ProgramUpdate, ProgramResource, ProgramParticipant, ProgramEvent
)
from .serializers import (
    ProgramCategorySerializer, ProgramSerializer, ProgramDetailSerializer,
    ProgramApplicationSerializer, ProgramApplicationCreateSerializer,
    ProgramUpdateSerializer, ProgramResourceSerializer,
    ProgramParticipantSerializer, ProgramEventSerializer,
    PublicProgramSerializer, PublicProgramCategorySerializer
)

logger = logging.getLogger(__name__)


class ProgramCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for program categories
    """
    queryset = ProgramCategory.objects.filter(is_active=True)
    serializer_class = ProgramCategorySerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return PublicProgramCategorySerializer
        return ProgramCategorySerializer
    
    @action(detail=True, methods=['get'])
    def programs(self, request, slug=None):
        """Get all programs in a category"""
        category = self.get_object()
        programs = Program.objects.filter(
            category=category,
            is_published=True
        ).order_by('-is_featured', '-created_at')
        
        page = self.paginate_queryset(programs)
        if page is not None:
            serializer = PublicProgramSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = PublicProgramSerializer(programs, many=True, context={'request': request})
        return Response(serializer.data)


class ProgramViewSet(viewsets.ModelViewSet):
    """
    ViewSet for programs
    """
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'program_type', 'status', 'location_type', 'is_featured']
    search_fields = ['title', 'short_description', 'full_description', 'objectives']
    ordering_fields = ['created_at', 'start_date', 'views', 'current_participants']
    ordering = ['-created_at']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProgramDetailSerializer
        elif self.action in ['list']:
            return PublicProgramSerializer
        return ProgramSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ['list', 'retrieve']:
            queryset = queryset.filter(is_published=True)
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve program and increment view count"""
        instance = self.get_object()
        instance.views += 1
        instance.save(update_fields=['views'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured programs"""
        queryset = self.get_queryset().filter(is_featured=True, is_published=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming programs"""
        queryset = self.get_queryset().filter(
            is_published=True,
            start_date__gt=timezone.now().date()
        ).order_by('start_date')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def ongoing(self, request):
        """Get ongoing programs"""
        today = timezone.now().date()
        queryset = self.get_queryset().filter(
            is_published=True,
            start_date__lte=today,
            end_date__gte=today
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def applications(self, request, slug=None):
        """Get applications for this program"""
        program = self.get_object()
        if not request.user.is_staff and request.user != program.program_lead:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        applications = program.applications.all()
        serializer = ProgramApplicationSerializer(applications, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def participants(self, request, slug=None):
        """Get participants for this program"""
        program = self.get_object()
        participants = program.participants.all()
        serializer = ProgramParticipantSerializer(participants, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def resources(self, request, slug=None):
        """Get resources for this program"""
        program = self.get_object()
        
        # Check access
        user = request.user
        if not user.is_authenticated:
            resources = program.resources.filter(is_public=True)
        elif program.participants.filter(user=user, status='active').exists():
            resources = program.resources.filter(
                Q(is_public=True) | Q(access_level__in=['all', 'accepted'])
            )
        else:
            resources = program.resources.filter(is_public=True)
        
        serializer = ProgramResourceSerializer(resources, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def events(self, request, slug=None):
        """Get events for this program"""
        program = self.get_object()
        events = program.events.filter(is_published=True).order_by('start_datetime')
        serializer = ProgramEventSerializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def apply(self, request, slug=None):
        """Apply to a program"""
        program = self.get_object()
        user = request.user
        
        # Check if program accepts applications
        if program.application_deadline and program.application_deadline < timezone.now().date():
            return Response(
                {'error': 'Application deadline has passed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already applied
        existing_application = program.applications.filter(applicant=user).first()
        if existing_application:
            return Response(
                {'error': 'You have already applied to this program'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already a participant
        existing_participant = program.participants.filter(user=user).exists()
        if existing_participant:
            return Response(
                {'error': 'You are already a participant in this program'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ProgramApplicationCreateSerializer(
            data=request.data,
            context={'program': program, 'user': user}
        )
        
        if serializer.is_valid():
            application = serializer.save()
            
            # Send confirmation email
            self.send_application_confirmation(application)
            
            return Response(
                ProgramApplicationSerializer(application).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def send_application_confirmation(self, application):
        """Send confirmation email for application"""
        subject = f'Application Received: {application.program.title}'
        message = f"""
        Dear {application.applicant.get_full_name() or application.applicant.username},
        
        Thank you for applying to "{application.program.title}"!
        
        We have received your application and will review it shortly.
        You will be notified about the status of your application via email.
        
        Application Details:
        - Program: {application.program.title}
        - Applied on: {application.created_at.strftime('%B %d, %Y')}
        - Application ID: {application.uuid}
        
        You can view your application status by logging into your account.
        
        Best regards,
        The YES Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[application.applicant.email],
            fail_silently=False,
        )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get program statistics"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        stats = {
            'total_programs': Program.objects.count(),
            'published_programs': Program.objects.filter(is_published=True).count(),
            'programs_by_type': Program.objects.values('program_type')
                .annotate(count=Count('id'))
                .order_by('-count'),
            'programs_by_status': Program.objects.values('status')
                .annotate(count=Count('id'))
                .order_by('-count'),
            'total_participants': ProgramParticipant.objects.count(),
            'total_applications': ProgramApplication.objects.count(),
            'completion_rate_avg': Program.objects.aggregate(
                avg=Avg('completion_rate')
            )['avg'] or 0,
            'upcoming_programs': Program.objects.filter(
                start_date__gt=timezone.now().date()
            ).count(),
        }
        
        return Response(stats)


class ProgramApplicationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for program applications
    """
    serializer_class = ProgramApplicationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'program']
    ordering_fields = ['submitted_at', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return ProgramApplication.objects.all()
        return ProgramApplication.objects.filter(applicant=user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ProgramApplicationCreateSerializer
        return ProgramApplicationSerializer
    
    def perform_create(self, serializer):
        application = serializer.save(applicant=self.request.user)
        
        # Send notification to program lead
        self.send_new_application_notification(application)
    
    def send_new_application_notification(self, application):
        """Send notification to program lead about new application"""
        program_lead = application.program.program_lead
        if program_lead and program_lead.email:
            subject = f'New Application: {application.program.title}'
            message = f"""
            New application received for program: {application.program.title}
            
            Applicant: {application.applicant.get_full_name() or application.applicant.username}
            Email: {application.applicant.email}
            Applied on: {application.created_at.strftime('%B %d, %Y %H:%M')}
            
            To review this application, please visit the admin panel.
            
            Application ID: {application.uuid}
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[program_lead.email],
                fail_silently=False,
            )


class ProgramParticipantViewSet(viewsets.ModelViewSet):
    """
    ViewSet for program participants
    """
    serializer_class = ProgramParticipantSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return ProgramParticipant.objects.all()
        return ProgramParticipant.objects.filter(user=user)
    
    @action(detail=False, methods=['get'])
    def my_programs(self, request):
        """Get current user's program participations"""
        user = request.user
        participations = ProgramParticipant.objects.filter(user=user)
        serializer = self.get_serializer(participations, many=True)
        return Response(serializer.data)


class ProgramEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for program events
    """
    queryset = ProgramEvent.objects.filter(is_published=True)
    serializer_class = ProgramEventSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['program', 'location_type']
    ordering_fields = ['start_datetime']
    ordering = ['start_datetime']
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming events"""
        queryset = self.get_queryset().filter(
            start_datetime__gt=timezone.now()
        ).order_by('start_datetime')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)