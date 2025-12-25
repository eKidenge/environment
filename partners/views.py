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
    PartnerOrganization, PartnershipAgreement, PartnershipProject,
    PartnerContact, PartnershipMeeting, PartnershipResource,
    PartnerEvaluation, PartnershipOpportunity
)
from .serializers import (
    PartnerOrganizationSerializer, PartnerOrganizationDetailSerializer,
    PartnershipAgreementSerializer, PartnershipProjectSerializer,
    PartnerContactSerializer, PartnershipMeetingSerializer,
    PartnershipResourceSerializer, PartnerEvaluationSerializer,
    PartnershipOpportunitySerializer, PublicPartnerOrganizationSerializer,
    PublicPartnershipProjectSerializer
)

logger = logging.getLogger(__name__)


class PartnerOrganizationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for partner organizations
    """
    queryset = PartnerOrganization.objects.all()
    serializer_class = PartnerOrganizationSerializer
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_type', 'partnership_level', 'status', 'country', 
                       'is_featured', 'is_public', 'show_on_website']
    search_fields = ['name', 'description', 'mission', 'focus_areas', 'city', 'country', 
                    'collaboration_areas', 'contact_person']
    ordering_fields = ['name', 'partnership_start', 'total_funding', 'created_at']
    ordering = ['display_order', 'name']
    
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
            return PartnerOrganizationDetailSerializer
        elif self.action in ['list']:
            return PublicPartnerOrganizationSerializer
        return PartnerOrganizationSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ['list', 'retrieve']:
            queryset = queryset.filter(is_public=True, show_on_website=True)
        return queryset
    
    @action(detail=True, methods=['get'])
    def agreements(self, request, slug=None):
        """Get agreements for this partner"""
        partner = self.get_object()
        
        # Check permissions
        if not request.user.is_staff and not partner.is_public:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        agreements = partner.agreements.all()
        serializer = PartnershipAgreementSerializer(agreements, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def projects(self, request, slug=None):
        """Get projects with this partner"""
        partner = self.get_object()
        projects = partner.projects.filter(is_public=True)
        serializer = PublicPartnershipProjectSerializer(projects, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def contacts(self, request, slug=None):
        """Get contacts for this partner"""
        partner = self.get_object()
        
        # Check permissions
        if not request.user.is_staff and not partner.is_public:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        contacts = partner.contacts.filter(is_active=True)
        serializer = PartnerContactSerializer(contacts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def resources(self, request, slug=None):
        """Get resources for this partner"""
        partner = self.get_object()
        
        # Filter resources based on confidentiality
        resources = partner.resources.all()
        if not request.user.is_staff:
            resources = resources.filter(
                Q(confidentiality_level='public') | 
                Q(confidentiality_level='internal')
            )
        
        serializer = PartnershipResourceSerializer(resources, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def evaluations(self, request, slug=None):
        """Get evaluations for this partner"""
        partner = self.get_object()
        
        # Check permissions
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        evaluations = partner.evaluations.all()
        serializer = PartnerEvaluationSerializer(evaluations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured partners"""
        queryset = self.get_queryset().filter(is_featured=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_country(self, request):
        """Get partners by country"""
        country = request.query_params.get('country')
        if not country:
            return Response(
                {'error': 'country parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(country__iexact=country)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get partners by organization type"""
        org_type = request.query_params.get('type')
        if not org_type:
            return Response(
                {'error': 'type parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(organization_type=org_type)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get partnership statistics"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        stats = {
            'total_partners': PartnerOrganization.objects.count(),
            'active_partners': PartnerOrganization.objects.filter(status='active').count(),
            'partners_by_type': PartnerOrganization.objects.values('organization_type')
                .annotate(count=Count('id'))
                .order_by('-count'),
            'partners_by_level': PartnerOrganization.objects.values('partnership_level')
                .annotate(count=Count('id'))
                .order_by('-count'),
            'partners_by_country': PartnerOrganization.objects.values('country')
                .annotate(count=Count('id'))
                .order_by('-count')[:10],
            'total_funding': PartnerOrganization.objects.aggregate(
                total=Sum('total_funding')
            )['total'] or 0,
            'total_in_kind_value': PartnerOrganization.objects.aggregate(
                total=Sum('in_kind_value')
            )['total'] or 0,
            'total_projects_supported': PartnerOrganization.objects.aggregate(
                total=Sum('projects_supported')
            )['total'] or 0,
            'active_partnerships_count': PartnerOrganization.objects.filter(
                Q(status='active'),
                Q(partnership_end__isnull=True) | Q(partnership_end__gte=timezone.now().date())
            ).count(),
            'expiring_soon': PartnerOrganization.objects.filter(
                Q(status='active'),
                Q(partnership_end__gte=timezone.now().date()),
                Q(partnership_end__lte=timezone.now().date() + timedelta(days=90))
            ).count(),
        }
        
        return Response(stats)


class PartnershipProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for partnership projects
    """
    queryset = PartnershipProject.objects.all()
    serializer_class = PartnershipProjectSerializer
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'is_featured', 'is_public', 'thematic_areas']
    search_fields = ['title', 'description', 'partner__name', 'program__title', 'thematic_areas']
    ordering_fields = ['start_date', 'created_at', 'budget']
    ordering = ['-start_date']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return PublicPartnershipProjectSerializer
        return PartnershipProjectSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ['list', 'retrieve']:
            queryset = queryset.filter(is_public=True)
        return queryset
    
    @action(detail=True, methods=['get'])
    def meetings(self, request, slug=None):
        """Get meetings for this project"""
        project = self.get_object()
        
        # Check permissions
        if not request.user.is_staff and not project.is_public:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        meetings = project.meetings.all()
        serializer = PartnershipMeetingSerializer(meetings, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def resources(self, request, slug=None):
        """Get resources for this project"""
        project = self.get_object()
        resources = project.resources.all()
        
        # Filter based on confidentiality
        if not request.user.is_staff:
            resources = resources.filter(
                Q(confidentiality_level='public') | 
                Q(confidentiality_level='internal')
            )
        
        serializer = PartnershipResourceSerializer(resources, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active partnership projects"""
        queryset = self.get_queryset().filter(status='active', is_public=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_partner(self, request):
        """Get projects by partner"""
        partner_id = request.query_params.get('partner_id')
        if not partner_id:
            return Response(
                {'error': 'partner_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(partner_id=partner_id, is_public=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PartnershipAgreementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for partnership agreements
    """
    queryset = PartnershipAgreement.objects.all()
    serializer_class = PartnershipAgreementSerializer
    permission_classes = [IsAdminUser]  # Only staff can access agreements
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by partner if provided
        partner_id = self.request.query_params.get('partner_id')
        if partner_id:
            queryset = queryset.filter(partner_id=partner_id)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def sign(self, request, pk=None):
        """Sign an agreement"""
        agreement = self.get_object()
        
        if agreement.status != 'ready_for_signature':
            return Response(
                {'error': f'Agreement is not ready for signature (current: {agreement.get_status_display()})'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update agreement
        agreement.status = 'signed'
        agreement.signed_date = timezone.now().date()
        agreement.our_signatory = request.user
        agreement.save()
        
        # Update partner agreement status
        partner = agreement.partner
        partner.agreement_status = 'signed'
        if not partner.partnership_start:
            partner.partnership_start = agreement.effective_date
        partner.save()
        
        # Send notification
        self.send_agreement_signed_notification(agreement)
        
        return Response({'status': 'Agreement signed successfully'})
    
    def send_agreement_signed_notification(self, agreement):
        """Send notification about signed agreement"""
        # This could be implemented to notify relevant parties
        pass


class PartnerContactViewSet(viewsets.ModelViewSet):
    """
    ViewSet for partner contacts
    """
    serializer_class = PartnerContactSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return PartnerContact.objects.all()
        
        # Non-staff can only see contacts of partners they work with
        # This would need custom logic based on user's projects/assignments
        return PartnerContact.objects.none()
    
    @action(detail=False, methods=['get'])
    def my_contacts(self, request):
        """Get contacts for partners the user works with"""
        user = request.user
        
        # Get partners where user is focal point or project lead
        partners = PartnerOrganization.objects.filter(
            Q(focal_point=user) |
            Q(projects__project_lead=user) |
            Q(projects__team_members=user)
        ).distinct()
        
        contacts = PartnerContact.objects.filter(
            partner__in=partners,
            is_active=True
        )
        
        serializer = self.get_serializer(contacts, many=True)
        return Response(serializer.data)


class PartnershipMeetingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for partnership meetings
    """
    serializer_class = PartnershipMeetingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return PartnershipMeeting.objects.all()
        
        # Users can see meetings they're part of or for partners they work with
        return PartnershipMeeting.objects.filter(
            Q(yes_team=user) |
            Q(partner__focal_point=user) |
            Q(project__project_lead=user) |
            Q(project__team_members=user)
        ).distinct()
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark a meeting as completed"""
        meeting = self.get_object()
        
        # Check permission
        if (request.user not in meeting.yes_team.all() and 
            not request.user.is_staff):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if meeting.status in ['completed', 'cancelled']:
            return Response(
                {'error': f'Meeting already {meeting.get_status_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        meeting.status = 'completed'
        meeting.save()
        
        return Response({'status': 'Meeting marked as completed'})
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming meetings"""
        queryset = self.get_queryset().filter(
            scheduled_date__gte=timezone.now().date(),
            status__in=['scheduled', 'confirmed']
        ).order_by('scheduled_date', 'scheduled_time')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PartnershipResourceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for partnership resources
    """
    serializer_class = PartnershipResourceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = PartnershipResource.objects.all()
        
        if not user.is_staff:
            # Non-staff can only see public or internal resources
            queryset = queryset.filter(
                Q(confidentiality_level='public') | 
                Q(confidentiality_level='internal')
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def download(self, request, pk=None):
        """Record a resource download"""
        resource = self.get_object()
        
        # Check access
        if (resource.confidentiality_level == 'restricted' and 
            not request.user.is_staff):
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        resource.download_count += 1
        resource.save(update_fields=['download_count'])
        
        logger.info(f"Resource {resource.title} downloaded by {request.user}")
        return Response({'status': 'Download recorded'})


class PartnerEvaluationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for partner evaluations
    """
    serializer_class = PartnerEvaluationSerializer
    permission_classes = [IsAdminUser]  # Only staff can access evaluations
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by partner if provided
        partner_id = self.request.query_params.get('partner_id')
        if partner_id:
            queryset = queryset.filter(partner_id=partner_id)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def finalize(self, request, pk=None):
        """Finalize an evaluation"""
        evaluation = self.get_object()
        
        if evaluation.is_finalized:
            return Response(
                {'error': 'Evaluation is already finalized'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        evaluation.is_finalized = True
        evaluation.finalized_at = timezone.now()
        evaluation.save()
        
        # Update partner score
        partner = evaluation.partner
        partner.partner_score = evaluation.average_rating() * 20  # Convert 1-5 to 0-100
        partner.save(update_fields=['partner_score'])
        
        return Response({'status': 'Evaluation finalized'})


class PartnershipOpportunityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for partnership opportunities
    """
    serializer_class = PartnershipOpportunitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return PartnershipOpportunity.objects.all()
        
        # Users can see opportunities assigned to them
        return PartnershipOpportunity.objects.filter(
            Q(assigned_to=user) | Q(team_members=user)
        ).distinct()
    
    @action(detail=True, methods=['post'])
    def convert_to_partner(self, request, pk=None):
        """Convert an opportunity to an actual partner"""
        opportunity = self.get_object()
        
        if opportunity.status != 'won':
            return Response(
                {'error': 'Only won opportunities can be converted to partners'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if opportunity.converted_partner:
            return Response(
                {'error': 'Opportunity already converted to partner'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create new partner
        partner = PartnerOrganization.objects.create(
            name=opportunity.organization_name or opportunity.name,
            organization_type=opportunity.organization_type,
            partnership_level=opportunity.potential_partnership_level,
            status='prospect',
            description=opportunity.description,
            contact_person=opportunity.contact_name,
            contact_email=opportunity.contact_email or '',
            contact_phone=opportunity.contact_phone or '',
            created_by=request.user
        )
        
        # Link opportunity to partner
        opportunity.converted_partner = partner
        opportunity.save()
        
        serializer = PartnerOrganizationSerializer(partner)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def pipeline(self, request):
        """Get opportunity pipeline statistics"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        pipeline = {
            'total_opportunities': PartnershipOpportunity.objects.count(),
            'by_status': PartnershipOpportunity.objects.values('status')
                .annotate(count=Count('id'), total_value=Sum('potential_value'))
                .order_by('-count'),
            'by_priority': PartnershipOpportunity.objects.values('priority')
                .annotate(count=Count('id'), total_value=Sum('potential_value'))
                .order_by('-count'),
            'total_potential_value': PartnershipOpportunity.objects.aggregate(
                total=Sum('potential_value')
            )['total'] or 0,
            'won_opportunities': PartnershipOpportunity.objects.filter(status='won')
                .aggregate(count=Count('id'), total_value=Sum('potential_value')),
            'upcoming_close_dates': PartnershipOpportunity.objects.filter(
                target_close_date__gte=timezone.now().date(),
                target_close_date__lte=timezone.now().date() + timedelta(days=30)
            ).count(),
        }
        
        return Response(pipeline)