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
    MentorshipProgram, MentorshipApplication, MentorshipMatch,
    MentorshipSession, MentorshipResource, MentorshipFeedback,
    MentorshipGoal
)
from .serializers import (
    MentorshipProgramSerializer, MentorshipProgramDetailSerializer,
    MentorshipApplicationSerializer, MentorshipApplicationCreateSerializer,
    MentorshipMatchSerializer, MentorshipSessionSerializer,
    MentorshipResourceSerializer, MentorshipFeedbackSerializer,
    MentorshipGoalSerializer, PublicMentorshipProgramSerializer,
    PublicMentorshipResourceSerializer
)

logger = logging.getLogger(__name__)


class MentorshipProgramViewSet(viewsets.ModelViewSet):
    """
    ViewSet for mentorship programs
    """
    queryset = MentorshipProgram.objects.all()
    serializer_class = MentorshipProgramSerializer
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['program_type', 'status', 'format', 'is_featured']
    search_fields = ['title', 'description', 'objectives', 'skills_focus']
    ordering_fields = ['program_start', 'application_deadline', 'created_at']
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
            return MentorshipProgramDetailSerializer
        elif self.action in ['list']:
            return PublicMentorshipProgramSerializer
        return MentorshipProgramSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ['list', 'retrieve']:
            queryset = queryset.filter(is_published=True)
        return queryset
    
    @action(detail=True, methods=['get'])
    def applications(self, request, slug=None):
        """Get applications for this program"""
        program = self.get_object()
        user = request.user
        
        # Check permissions
        if not user.is_staff and user != program.program_coordinator:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        applications = program.applications.all()
        serializer = MentorshipApplicationSerializer(applications, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def matches(self, request, slug=None):
        """Get matches for this program"""
        program = self.get_object()
        user = request.user
        
        # Check permissions
        if not user.is_staff and user != program.program_coordinator:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        matches = program.matches.all()
        serializer = MentorshipMatchSerializer(matches, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def resources(self, request, slug=None):
        """Get resources for this program"""
        program = self.get_object()
        resources = program.program_resources.filter(access_level__in=['public', 'program'])
        serializer = PublicMentorshipResourceSerializer(resources, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def apply(self, request, slug=None):
        """Apply to a mentorship program"""
        program = self.get_object()
        user = request.user
        
        if not user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if program is accepting applications
        if not program.is_accepting_applications():
            return Response(
                {'error': 'Program is not currently accepting applications'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already applied
        existing_application = program.applications.filter(applicant=user).first()
        if existing_application:
            return Response(
                {'error': 'You have already applied to this program'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already a mentor in this program
        if user in program.mentors.all():
            return Response(
                {'error': 'You are already a mentor in this program'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = MentorshipApplicationCreateSerializer(
            data=request.data,
            context={'program': program, 'user': user}
        )
        
        if serializer.is_valid():
            application = serializer.save()
            
            # Send confirmation email
            self.send_application_confirmation(application)
            
            # Update application count
            program.applications_count += 1
            program.save(update_fields=['applications_count'])
            
            return Response(
                MentorshipApplicationSerializer(application).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def send_application_confirmation(self, application):
        """Send confirmation email for mentorship application"""
        subject = f'Application Received: {application.program.title}'
        message = f"""
        Dear {application.applicant.get_full_name() or application.applicant.username},
        
        Thank you for applying to the "{application.program.title}" mentorship program!
        
        We have received your application and will review it shortly.
        You will be notified about the status of your application via email.
        
        Application Details:
        - Program: {application.program.title}
        - Role: {application.get_applying_as_display()}
        - Applied on: {application.created_at.strftime('%B %d, %Y')}
        - Application ID: {application.uuid}
        
        You can view your application status by logging into your account.
        
        Best regards,
        The YES Mentorship Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[application.applicant.email],
            fail_silently=False,
        )
    
    @action(detail=False, methods=['get'])
    def open_for_applications(self, request):
        """Get programs currently open for applications"""
        today = timezone.now().date()
        queryset = self.get_queryset().filter(
            is_published=True,
            application_start__lte=today,
            application_deadline__gte=today
        ).order_by('application_deadline')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming mentorship programs"""
        today = timezone.now().date()
        queryset = self.get_queryset().filter(
            is_published=True,
            program_start__gt=today
        ).order_by('program_start')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class MentorshipApplicationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for mentorship applications
    """
    serializer_class = MentorshipApplicationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'program', 'applying_as']
    ordering_fields = ['submitted_at', 'created_at', 'review_score']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return MentorshipApplication.objects.all()
        return MentorshipApplication.objects.filter(applicant=user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MentorshipApplicationCreateSerializer
        return MentorshipApplicationSerializer
    
    def perform_create(self, serializer):
        application = serializer.save(applicant=self.request.user)
        
        # Send notification to program coordinator
        self.send_new_application_notification(application)
    
    def send_new_application_notification(self, application):
        """Send notification to program coordinator about new application"""
        coordinator = application.program.program_coordinator
        if coordinator and coordinator.email:
            subject = f'New Mentorship Application: {application.program.title}'
            message = f"""
            New mentorship application received for program: {application.program.title}
            
            Applicant: {application.applicant.get_full_name() or application.applicant.username}
            Email: {application.applicant.email}
            Role: {application.get_applying_as_display()}
            Applied on: {application.created_at.strftime('%B %d, %Y %H:%M')}
            
            To review this application, please visit the admin panel.
            
            Application ID: {application.uuid}
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[coordinator.email],
                fail_silently=False,
            )
    
    @action(detail=True, methods=['post'])
    def withdraw(self, request, pk=None):
        """Withdraw an application"""
        application = self.get_object()
        
        # Check permission
        if application.applicant != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if application.status in ['accepted', 'withdrawn']:
            return Response(
                {'error': f'Cannot withdraw application in {application.get_status_display()} status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        application.status = 'withdrawn'
        application.save()
        
        return Response({'status': 'Application withdrawn successfully'})


class MentorshipMatchViewSet(viewsets.ModelViewSet):
    """
    ViewSet for mentorship matches
    """
    serializer_class = MentorshipMatchSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return MentorshipMatch.objects.all()
        
        # Users can see matches where they are mentor or mentee
        return MentorshipMatch.objects.filter(
            Q(mentor=user) | Q(mentee=user)
        )
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept a proposed match"""
        match = self.get_object()
        
        # Check if user is mentee
        if match.mentee != request.user:
            return Response(
                {'error': 'Only mentee can accept the match'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if match.status != 'proposed':
            return Response(
                {'error': f'Match is not in proposed status (current: {match.get_status_display()})'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        match.status = 'accepted'
        match.accepted_at = timezone.now()
        match.save()
        
        # Send notification to mentor
        self.send_match_accepted_notification(match)
        
        return Response({'status': 'Match accepted successfully'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a proposed match"""
        match = self.get_object()
        
        # Check if user is mentee
        if match.mentee != request.user:
            return Response(
                {'error': 'Only mentee can reject the match'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if match.status != 'proposed':
            return Response(
                {'error': f'Match is not in proposed status (current: {match.get_status_display()})'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        match.status = 'rejected'
        match.save()
        
        return Response({'status': 'Match rejected'})
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start an accepted match"""
        match = self.get_object()
        
        # Check if user is mentor or mentee
        if match.mentor != request.user and match.mentee != request.user:
            return Response(
                {'error': 'Only mentor or mentee can start the match'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if match.status != 'accepted':
            return Response(
                {'error': f'Match must be accepted before starting (current: {match.get_status_display()})'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        match.status = 'active'
        match.started_at = timezone.now()
        match.save()
        
        return Response({'status': 'Match started successfully'})
    
    @action(detail=True, methods=['get'])
    def sessions(self, request, pk=None):
        """Get sessions for this match"""
        match = self.get_object()
        
        # Check permission
        if match.mentor != request.user and match.mentee != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        sessions = match.sessions.all()
        serializer = MentorshipSessionSerializer(sessions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def goals(self, request, pk=None):
        """Get goals for this match"""
        match = self.get_object()
        
        # Check permission
        if match.mentor != request.user and match.mentee != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        goals = match.goals.all()
        serializer = MentorshipGoalSerializer(goals, many=True)
        return Response(serializer.data)
    
    def send_match_accepted_notification(self, match):
        """Send notification to mentor about accepted match"""
        if match.mentor.email:
            subject = f'Match Accepted: {match.program.title}'
            message = f"""
            Your mentorship match has been accepted!
            
            Program: {match.program.title}
            Mentee: {match.mentee.get_full_name() or match.mentee.username}
            Email: {match.mentee.email}
            
            The match is now ready to begin. Please schedule your first session.
            
            Match ID: {match.uuid}
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[match.mentor.email],
                fail_silently=False,
            )


class MentorshipSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for mentorship sessions
    """
    serializer_class = MentorshipSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return MentorshipSession.objects.all()
        
        # Users can see sessions from their matches
        return MentorshipSession.objects.filter(
            Q(match__mentor=user) | Q(match__mentee=user)
        )
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark a session as completed"""
        session = self.get_object()
        
        # Check permission
        if session.match.mentor != request.user and session.match.mentee != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if session.status in ['completed', 'cancelled']:
            return Response(
                {'error': f'Session already {session.get_status_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session.status = 'completed'
        session.actual_end = timezone.now()
        if not session.actual_start:
            session.actual_start = session.actual_end - timedelta(hours=1)  # Default duration
        
        # Update match meetings count
        session.match.meetings_held += 1
        session.match.save(update_fields=['meetings_held'])
        
        session.save()
        
        return Response({'status': 'Session marked as completed'})
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a session"""
        session = self.get_object()
        
        # Check permission
        if session.match.mentor != request.user and session.match.mentee != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if session.status in ['completed', 'cancelled']:
            return Response(
                {'error': f'Session already {session.get_status_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session.status = 'cancelled'
        session.save()
        
        return Response({'status': 'Session cancelled'})


class MentorshipResourceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for mentorship resources
    """
    queryset = MentorshipResource.objects.filter(access_level__in=['public', 'program'])
    serializer_class = MentorshipResourceSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['resource_type', 'access_level']
    search_fields = ['title', 'description', 'content', 'tags']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.is_authenticated:
            # Authenticated users can see program resources
            queryset = queryset.filter(
                Q(access_level__in=['public', 'program']) |
                Q(access_level='match', match__mentor=user) |
                Q(access_level='match', match__mentee=user)
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def download(self, request, pk=None):
        """Record a resource download"""
        resource = self.get_object()
        
        # Check access
        if resource.access_level == 'private' and not request.user.is_staff:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        resource.download_count += 1
        resource.save(update_fields=['download_count'])
        
        logger.info(f"Resource {resource.title} downloaded by {request.user}")
        return Response({'status': 'Download recorded'})


class MentorshipFeedbackViewSet(viewsets.ModelViewSet):
    """
    ViewSet for mentorship feedback
    """
    serializer_class = MentorshipFeedbackSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return MentorshipFeedback.objects.all()
        
        # Users can see feedback they provided or received
        return MentorshipFeedback.objects.filter(
            Q(provided_by=user) | Q(provided_for=user)
        )
    
    def perform_create(self, serializer):
        feedback = serializer.save(provided_by=self.request.user)
        
        # Send notification if feedback is about someone
        if feedback.provided_for:
            self.send_feedback_notification(feedback)
    
    def send_feedback_notification(self, feedback):
        """Send notification about feedback"""
        # This could be implemented to notify the recipient
        pass


class MentorshipGoalViewSet(viewsets.ModelViewSet):
    """
    ViewSet for mentorship goals
    """
    serializer_class = MentorshipGoalSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return MentorshipGoal.objects.all()
        
        # Users can see goals from their matches
        return MentorshipGoal.objects.filter(
            Q(match__mentor=user) | Q(match__mentee=user)
        )
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Update goal progress"""
        goal = self.get_object()
        
        # Check permission
        if goal.match.mentor != request.user and goal.match.mentee != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        progress = request.data.get('progress_percentage')
        if progress is None:
            return Response(
                {'error': 'progress_percentage is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            progress = float(progress)
            if not 0 <= progress <= 100:
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {'error': 'progress_percentage must be a number between 0 and 100'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        goal.progress_percentage = progress
        
        # Update status based on progress
        if progress >= 100:
            goal.status = 'completed'
            goal.completion_date = timezone.now().date()
        elif progress > 0:
            goal.status = 'in_progress'
            if not goal.start_date:
                goal.start_date = timezone.now().date()
        
        goal.save()
        
        # Update match milestones if completed
        if goal.status == 'completed':
            goal.match.milestones_completed += 1
            goal.match.save(update_fields=['milestones_completed'])
        
        return Response(MentorshipGoalSerializer(goal).data)