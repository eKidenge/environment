from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta
import logging

from .models import CustomUser, UserActivityLog, UserVerification
from .serializers import (
    UserSerializer, UserProfileSerializer, UserCreateSerializer,
    UserUpdateSerializer, UserActivityLogSerializer, UserVerificationSerializer,
    UserStatsSerializer
)

logger = logging.getLogger(__name__)

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing user instances.
    """
    queryset = CustomUser.objects.filter(is_deleted=False)
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user_type', 'verification_status', 'country', 'city', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'organization']
    ordering_fields = ['date_joined', 'last_login', 'contribution_score', 'username']
    ordering = ['-date_joined']
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'profile':
            return UserProfileSerializer
        return UserSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create a new user (registration)
        """
        print("=== REGISTRATION STARTED ===")
        print("Request data:", request.data)
        
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            print("Serializer is valid")
            try:
                user = serializer.save()
                print(f"✅ User created: {user.username} (ID: {user.id})")
                print(f"Email: {user.email}, Name: {user.first_name} {user.last_name}")
                
                # Log registration activity
                UserActivityLog.objects.create(
                    user=user,
                    activity_type='registration',
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    details={'source': 'web_registration'}
                )
                print("✅ Activity log created")
                
                # Return success response
                headers = self.get_success_headers(serializer.data)
                print("=== REGISTRATION COMPLETED SUCCESSFULLY ===")
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED,
                    headers=headers
                )
                
            except Exception as e:
                print(f"❌ Error creating user: {str(e)}")
                logger.error(f"Registration error: {str(e)}")
                print("=== REGISTRATION FAILED ===")
                return Response(
                    {'detail': 'Registration failed. Please try again.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        print("❌ Serializer errors:", serializer.errors)
        print("=== REGISTRATION VALIDATION FAILED ===")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def profile(self, request):
        """
        Get current user's profile
        """
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        """
        Update current user's profile
        """
        serializer = UserProfileSerializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            # Log activity
            UserActivityLog.objects.create(
                user=request.user,
                activity_type='profile_update',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                details={'updated_fields': list(request.data.keys())}
            )
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def stats(self, request):
        """
        Get user statistics
        """
        # Time ranges
        today = timezone.now().date()
        last_7_days = today - timedelta(days=7)
        last_30_days = today - timedelta(days=30)
        
        stats = {
            'total_users': CustomUser.objects.filter(is_deleted=False).count(),
            'active_users': CustomUser.objects.filter(is_active=True, is_deleted=False).count(),
            'users_by_type': CustomUser.objects.filter(is_deleted=False)
                .values('user_type')
                .annotate(count=Count('id'))
                .order_by('-count'),
            'users_by_country': CustomUser.objects.filter(is_deleted=False, country__isnull=False)
                .values('country')
                .annotate(count=Count('id'))
                .order_by('-count')[:10],
            'recent_signups': CustomUser.objects.filter(
                is_deleted=False,
                date_joined__date__gte=last_7_days
            ).count(),
            'verification_stats': {
                'pending': CustomUser.objects.filter(
                    verification_status='pending',
                    is_deleted=False
                ).count(),
                'verified': CustomUser.objects.filter(
                    verification_status='verified',
                    is_deleted=False
                ).count(),
                'rejected': CustomUser.objects.filter(
                    verification_status='rejected',
                    is_deleted=False
                ).count(),
            },
            'top_contributors': CustomUser.objects.filter(
                is_deleted=False
            ).order_by('-contribution_score')[:10].values(
                'username', 'contribution_score', 'user_type'
            ),
            'activity_last_24h': UserActivityLog.objects.filter(
                timestamp__gte=timezone.now() - timedelta(hours=24)
            ).count(),
        }
        
        serializer = UserStatsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def verify(self, request, pk=None):
        """
        Verify a user
        """
        user = self.get_object()
        if user.verification_status == 'verified':
            return Response(
                {'error': 'User is already verified'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.verification_status = 'verified'
        user.verified_by = request.user
        user.save()
        
        # Create verification record if exists
        verification, created = UserVerification.objects.get_or_create(
            user=user,
            defaults={
                'document_type': 'manual_verification',
                'is_approved': True,
                'verified_by': request.user,
                'verification_notes': 'Manually verified by admin'
            }
        )
        if not created:
            verification.is_approved = True
            verification.verified_by = request.user
            verification.verified_at = timezone.now()
            verification.verification_notes = 'Manually verified by admin'
            verification.save()
        
        logger.info(f"User {user.username} verified by {request.user.username}")
        return Response({'status': 'User verified successfully'})
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class UserActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing user activity logs
    """
    serializer_class = UserActivityLogSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['activity_type', 'user']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        queryset = UserActivityLog.objects.all()
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset

class UserVerificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user verifications
    """
    queryset = UserVerification.objects.all()
    serializer_class = UserVerificationSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_approved', 'document_type']
    search_fields = ['user__username', 'user__email', 'verification_notes']
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        verification = self.get_object()
        verification.is_approved = True
        verification.verified_by = request.user
        verification.verified_at = timezone.now()
        verification.save()
        
        # Update user status
        user = verification.user
        user.verification_status = 'verified'
        user.save()
        
        return Response({'status': 'Verification approved'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        verification = self.get_object()
        verification.is_approved = False
        verification.verified_by = request.user
        verification.verified_at = timezone.now()
        verification.verification_notes = request.data.get('reason', '')
        verification.save()
        
        # Update user status
        user = verification.user
        user.verification_status = 'rejected'
        user.save()
        
        return Response({'status': 'Verification rejected'})


# ===== LOGIN API VIEW =====
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login as auth_login
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

class LoginAPIView(APIView):
    """
    API endpoint for user login
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        print("=== LOGIN ATTEMPT ===")
        print("Login data:", request.data)
        
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': 'Please provide both username and password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Try to authenticate
        user = authenticate(username=username, password=password)
        
        if user:
            if not user.is_active:
                return Response(
                    {'error': 'Account is disabled. Please contact support.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Perform Django login to establish session (NEW LINE)
            auth_login(request, user)
            
            # Update user's last login
            user.last_login = timezone.now()
            user.save()
            
            # Log login activity
            UserActivityLog.objects.create(
                user=user,
                activity_type='login',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                details={'method': 'web_login'}
            )
            
            print(f"✅ Login successful for user: {user.username}")
            
            # Redirect to dashboard template (CHANGED THIS SECTION)
            return redirect('users:dashboard_home')
            
            # Remove the old Response return:
            # return Response({
            #     'message': 'Login successful',
            #     'user': {
            #         'id': user.id,
            #         'username': user.username,
            #         'email': user.email,
            #         'first_name': user.first_name,
            #         'last_name': user.last_name,
            #         'user_type': user.user_type,
            #     },
            #     'tokens': {
            #         'refresh': str(refresh),
            #         'access': str(refresh.access_token),
            #     }
            # })
        
        print(f"❌ Login failed for username: {username}")
        return Response(
            {'error': 'Invalid username or password'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
