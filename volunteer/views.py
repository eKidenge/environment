from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Avg, Sum, F
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
import logging

from .models import (
    VolunteerOpportunity, VolunteerApplication, VolunteerAssignment,
    VolunteerTimeLog, VolunteerSkill, VolunteerAward, VolunteerEvent
)
from .serializers import (
    VolunteerOpportunitySerializer, VolunteerOpportunityDetailSerializer,
    VolunteerApplicationSerializer, VolunteerApplicationCreateSerializer,
    VolunteerAssignmentSerializer, VolunteerTimeLogSerializer,
    VolunteerSkillSerializer, VolunteerAwardSerializer,
    VolunteerEventSerializer, PublicVolunteerOpportunitySerializer,
    PublicVolunteerEventSerializer
)

logger = logging.getLogger(__name__)


class VolunteerOpportunityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for volunteer opportunities
    """
    queryset = VolunteerOpportunity.objects.all()
    serializer_class = VolunteerOpportunitySerializer
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['opportunity_type', 'status', 'skill_level', 'country', 
                       'city', 'is_featured', 'remote_allowed']
    search_fields = ['title', 'description', 'responsibilities', 'city', 'country', 
                    'skills_required', 'skills_preferred']
    ordering_fields = ['created_at', 'start_date', 'application_deadline', 'views']
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
            return VolunteerOpportunityDetailSerializer
        elif self.action in ['list']:
            return PublicVolunteerOpportunitySerializer
        return VolunteerOpportunitySerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ['list', 'retrieve']:
            queryset = queryset.filter(is_published=True, status='published')
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve opportunity and increment view count"""
        instance = self.get_object()
        instance.views += 1
        instance.save(update_fields=['views'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def applications(self, request, slug=None):
        """Get applications for this opportunity"""
        opportunity = self.get_object()
        user = request.user
        
        # Check permissions
        if not user.is_staff and user != opportunity.team_lead and user != opportunity.supervisor:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        applications = opportunity.applications.all()
        serializer = VolunteerApplicationSerializer(applications, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def apply(self, request, slug=None):
        """Apply to a volunteer opportunity"""
        opportunity = self.get_object()
        user = request.user
        
        if not user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if opportunity is accepting applications
        if not opportunity.is_accepting_applications():
            return Response(
                {'error': 'Opportunity is not currently accepting applications'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already applied
        existing_application = opportunity.applications.filter(applicant=user).first()
        if existing_application:
            return Response(
                {'error': 'You have already applied to this opportunity'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check age requirements if specified
        if opportunity.min_age or opportunity.max_age:
            profile = user.userprofile if hasattr(user, 'userprofile') else None
            if profile and profile.date_of_birth:
                age = (timezone.now().date() - profile.date_of_birth).days // 365
                if opportunity.min_age and age < opportunity.min_age:
                    return Response(
                        {'error': f'Minimum age requirement is {opportunity.min_age} years'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if opportunity.max_age and age > opportunity.max_age:
                    return Response(
                        {'error': f'Maximum age requirement is {opportunity.max_age} years'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        
        serializer = VolunteerApplicationCreateSerializer(
            data=request.data,
            context={'opportunity': opportunity, 'user': user}
        )
        
        if serializer.is_valid():
            application = serializer.save()
            
            # Send confirmation email
            self.send_application_confirmation(application)
            
            # Update application count
            opportunity.applications_count += 1
            opportunity.save(update_fields=['applications_count'])
            
            return Response(
                VolunteerApplicationSerializer(application).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def send_application_confirmation(self, application):
        """Send confirmation email for volunteer application"""
        subject = f'Application Received: {application.opportunity.title}'
        message = f"""
        Dear {application.applicant.get_full_name() or application.applicant.username},
        
        Thank you for applying to volunteer for: "{application.opportunity.title}"
        
        We have received your application and will review it shortly.
        You will be notified about the status of your application via email.
        
        Application Details:
        - Opportunity: {application.opportunity.title}
        - Location: {application.opportunity.city}, {application.opportunity.country}
        - Applied on: {application.created_at.strftime('%B %d, %Y')}
        - Application ID: {application.uuid}
        
        You can view your application status by logging into your account.
        
        Best regards,
        The YES Volunteer Team
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
        """Get opportunities currently open for applications"""
        today = timezone.now().date()
        queryset = self.get_queryset().filter(
            is_published=True,
            status='published'
        ).filter(
            Q(application_deadline__isnull=True) | Q(application_deadline__gte=today),
            positions_filled__lt=F('positions_available')
        ).order_by('application_deadline')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def virtual(self, request):
        """Get virtual volunteer opportunities"""
        queryset = self.get_queryset().filter(
            opportunity_type='virtual',
            remote_allowed=True
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_location(self, request):
        """Get opportunities by location"""
        country = request.query_params.get('country')
        city = request.query_params.get('city')
        
        queryset = self.get_queryset()
        
        if country:
            queryset = queryset.filter(country__iexact=country)
        if city:
            queryset = queryset.filter(city__iexact=city)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get volunteer opportunity statistics"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        stats = {
            'total_opportunities': VolunteerOpportunity.objects.count(),
            'published_opportunities': VolunteerOpportunity.objects.filter(is_published=True).count(),
            'opportunities_by_type': VolunteerOpportunity.objects.filter(is_published=True)
                .values('opportunity_type')
                .annotate(count=Count('id'))
                .order_by('-count'),
            'opportunities_by_country': VolunteerOpportunity.objects.filter(
                is_published=True, 
                country__isnull=False
            ).values('country')
                .annotate(count=Count('id'))
                .order_by('-count')[:10],
            'total_positions_available': VolunteerOpportunity.objects.filter(is_published=True)
                .aggregate(total=Sum('positions_available'))['total'] or 0,
            'total_positions_filled': VolunteerOpportunity.objects.filter(is_published=True)
                .aggregate(total=Sum('positions_filled'))['total'] or 0,
            'total_applications': VolunteerApplication.objects.count(),
            'upcoming_deadlines': VolunteerOpportunity.objects.filter(
                is_published=True,
                application_deadline__gte=timezone.now().date()
            ).count(),
        }
        
        return Response(stats)


class VolunteerApplicationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for volunteer applications
    """
    serializer_class = VolunteerApplicationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'opportunity', 'availability_type', 
                       'background_check_status', 'training_status']
    ordering_fields = ['submitted_at', 'created_at', 'review_score']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return VolunteerApplication.objects.all()
        return VolunteerApplication.objects.filter(applicant=user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return VolunteerApplicationCreateSerializer
        return VolunteerApplicationSerializer
    
    def perform_create(self, serializer):
        application = serializer.save(applicant=self.request.user)
        
        # Send notification to supervisor/team lead
        self.send_new_application_notification(application)
    
    def send_new_application_notification(self, application):
        """Send notification about new volunteer application"""
        opportunity = application.opportunity
        supervisor = opportunity.supervisor
        team_lead = opportunity.team_lead
        
        recipients = []
        if supervisor and supervisor.email:
            recipients.append(supervisor.email)
        if team_lead and team_lead.email and team_lead.email != supervisor.email:
            recipients.append(team_lead.email)
        
        if recipients:
            subject = f'New Volunteer Application: {opportunity.title}'
            message = f"""
            New volunteer application received for: {opportunity.title}
            
            Applicant: {application.applicant.get_full_name() or application.applicant.username}
            Email: {application.applicant.email}
            Availability: {application.get_availability_type_display()}
            Applied on: {application.created_at.strftime('%B %d, %Y %H:%M')}
            
            To review this application, please visit the admin panel.
            
            Application ID: {application.uuid}
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=False,
            )
    
    @action(detail=True, methods=['post'])
    def withdraw(self, request, pk=None):
        """Withdraw a volunteer application"""
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
    
    @action(detail=True, methods=['get'])
    def assignment(self, request, pk=None):
        """Get assignment for this application"""
        application = self.get_object()
        
        # Check permission
        if application.applicant != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if hasattr(application, 'assignment'):
            serializer = VolunteerAssignmentSerializer(application.assignment)
            return Response(serializer.data)
        
        return Response({'detail': 'No assignment found'}, status=status.HTTP_404_NOT_FOUND)


class VolunteerAssignmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for volunteer assignments
    """
    serializer_class = VolunteerAssignmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return VolunteerAssignment.objects.all()
        
        # Users can see their own assignments or assignments they supervise
        return VolunteerAssignment.objects.filter(
            Q(application__applicant=user) | Q(supervisor=user)
        )
    
    @action(detail=True, methods=['get'])
    def time_logs(self, request, pk=None):
        """Get time logs for this assignment"""
        assignment = self.get_object()
        
        # Check permission
        if (assignment.application.applicant != request.user and 
            assignment.supervisor != request.user and 
            not request.user.is_staff):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        time_logs = assignment.time_logs.all()
        serializer = VolunteerTimeLogSerializer(time_logs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def log_time(self, request, pk=None):
        """Log time for this assignment"""
        assignment = self.get_object()
        
        # Check permission
        if assignment.application.applicant != request.user:
            return Response(
                {'error': 'Only the assigned volunteer can log time'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if assignment.status != 'active':
            return Response(
                {'error': f'Cannot log time for assignment in {assignment.get_status_display()} status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = VolunteerTimeLogSerializer(data=request.data)
        if serializer.is_valid():
            time_log = serializer.save(
                assignment=assignment,
                volunteer=request.user
            )
            
            # Update assignment hours
            assignment.hours_logged += time_log.total_hours
            assignment.save(update_fields=['hours_logged'])
            
            return Response(
                VolunteerTimeLogSerializer(time_log).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark assignment as completed"""
        assignment = self.get_object()
        
        # Check permission (supervisor or staff)
        if assignment.supervisor != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if assignment.status != 'active':
            return Response(
                {'error': f'Cannot complete assignment in {assignment.get_status_display()} status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        assignment.status = 'completed'
        assignment.actual_end_date = timezone.now().date()
        assignment.save()
        
        # Update opportunity positions filled
        opportunity = assignment.application.opportunity
        opportunity.positions_filled = min(
            opportunity.positions_filled + 1,
            opportunity.positions_available
        )
        opportunity.save(update_fields=['positions_filled'])
        
        return Response({'status': 'Assignment completed successfully'})


class VolunteerTimeLogViewSet(viewsets.ModelViewSet):
    """
    ViewSet for volunteer time logs
    """
    serializer_class = VolunteerTimeLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return VolunteerTimeLog.objects.all()
        
        # Users can see their own time logs or time logs they need to approve
        return VolunteerTimeLog.objects.filter(
            Q(volunteer=user) | Q(assignment__supervisor=user)
        )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a time log"""
        time_log = self.get_object()
        
        # Check permission (supervisor or staff)
        if time_log.assignment.supervisor != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if time_log.status != 'pending':
            return Response(
                {'error': f'Time log is already {time_log.get_status_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        time_log.status = 'approved'
        time_log.approved_by = request.user
        time_log.approved_at = timezone.now()
        time_log.save()
        
        return Response({'status': 'Time log approved'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a time log"""
        time_log = self.get_object()
        
        # Check permission (supervisor or staff)
        if time_log.assignment.supervisor != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if time_log.status != 'pending':
            return Response(
                {'error': f'Time log is already {time_log.get_status_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rejection_reason = request.data.get('rejection_reason', '')
        if not rejection_reason:
            return Response(
                {'error': 'Rejection reason is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        time_log.status = 'rejected'
        time_log.approved_by = request.user
        time_log.approved_at = timezone.now()
        time_log.rejection_reason = rejection_reason
        time_log.save()
        
        # Subtract hours from assignment
        time_log.assignment.hours_logged -= time_log.total_hours
        time_log.assignment.save(update_fields=['hours_logged'])
        
        return Response({'status': 'Time log rejected'})


class VolunteerSkillViewSet(viewsets.ModelViewSet):
    """
    ViewSet for volunteer skills
    """
    serializer_class = VolunteerSkillSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return VolunteerSkill.objects.all()
        return VolunteerSkill.objects.filter(volunteer=user)
    
    def perform_create(self, serializer):
        serializer.save(volunteer=self.request.user)


class VolunteerAwardViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for volunteer awards
    """
    serializer_class = VolunteerAwardSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = VolunteerAward.objects.filter(is_public=True)
        user = self.request.user
        
        if user.is_authenticated:
            # Authenticated users can see their own awards
            queryset = queryset | VolunteerAward.objects.filter(volunteer=user)
        
        return queryset.distinct()


class VolunteerEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for volunteer events
    """
    queryset = VolunteerEvent.objects.filter(is_published=True)
    serializer_class = VolunteerEventSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['event_type', 'location_type']
    ordering_fields = ['start_datetime']
    ordering = ['start_datetime']
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return PublicVolunteerEventSerializer
        return VolunteerEventSerializer
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming volunteer events"""
        queryset = self.get_queryset().filter(
            start_datetime__gt=timezone.now()
        ).order_by('start_datetime')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def register(self, request, slug=None):
        """Register for a volunteer event"""
        event = self.get_object()
        user = request.user
        
        if not user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not event.registration_required:
            return Response(
                {'error': 'Registration not required for this event'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if event.registration_deadline and event.registration_deadline < timezone.now():
            return Response(
                {'error': 'Registration deadline has passed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if event.max_attendees and event.current_attendees >= event.max_attendees:
            return Response(
                {'error': 'Event is full'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Increment attendees count
        event.current_attendees += 1
        event.save(update_fields=['current_attendees'])
        
        # Send confirmation email
        self.send_event_registration_confirmation(event, user)
        
        return Response({'status': 'Registered successfully'})
    
    def send_event_registration_confirmation(self, event, user):
        """Send confirmation email for event registration"""
        subject = f'Event Registration Confirmation: {event.title}'
        message = f"""
        Dear {user.get_full_name() or user.username},
        
        You have successfully registered for the event: "{event.title}"
        
        Event Details:
        - Date: {event.start_datetime.strftime('%B %d, %Y')}
        - Time: {event.start_datetime.strftime('%I:%M %p')} - {event.end_datetime.strftime('%I:%M %p')}
        - Location: {event.location.get('name', 'Virtual Event')}
        
        We look forward to seeing you there!
        
        Best regards,
        The YES Volunteer Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )