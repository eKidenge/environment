from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .views import (
    UserViewSet, 
    UserActivityLogViewSet, 
    UserVerificationViewSet, 
    LoginAPIView,
    login_view,  # Template-based login
    dashboard,   # Dashboard view
    profile_view, # Profile view
    logout_view   # Logout view
)
from django.views.generic import TemplateView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'activity-logs', UserActivityLogViewSet, basename='activitylog')
router.register(r'verifications', UserVerificationViewSet, basename='verification')

urlpatterns = [
    # API endpoints (keep existing)
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('login-api/', LoginAPIView.as_view(), name='login_api'),
    
    # Template-based views (add these)
    path('register/', TemplateView.as_view(template_name='users/register.html'), name='register'),
    path('login/', login_view, name='login'),  # Changed to function view
    path('dashboard/', dashboard, name='dashboard'),  # Add this line
    path('profile/', profile_view, name='profile'),  # Add this line
    path('logout/', logout_view, name='logout'),  # Add this line
]

app_name = 'users'
