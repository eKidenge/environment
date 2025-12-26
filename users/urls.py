from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .views import UserViewSet, UserActivityLogViewSet, UserVerificationViewSet, LoginAPIView
from django.views.generic import TemplateView
from django.contrib.auth.views import LogoutView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'activity-logs', UserActivityLogViewSet, basename='activitylog')
router.register(r'verifications', UserVerificationViewSet, basename='verification')

urlpatterns = [
    path('', include(router.urls)),
    
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Add registration page
    path('register/', TemplateView.as_view(template_name='users/register.html'), name='register'),
    
    # Add login page
    path('login/', TemplateView.as_view(template_name='users/login.html'), name='login'),
    path('login-api/', LoginAPIView.as_view(), name='login_api'),
    
    # Logout URL - Updated to redirect to home page
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    
    # Dashboard URL
    path('dashboard/home/', TemplateView.as_view(template_name='users/dashboard/home.html'), name='dashboard_home'),
]

# Add app_name for namespace support
app_name = 'users'
