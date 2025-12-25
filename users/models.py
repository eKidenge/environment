from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid

class CustomUser(AbstractUser):
    class UserType(models.TextChoices):
        ADMIN = 'admin', _('Administrator')
        STAFF = 'staff', _('Staff Member')
        VOLUNTEER = 'volunteer', _('Volunteer')
        MEMBER = 'member', _('Member')
        RESEARCHER = 'researcher', _('Researcher')
        MENTOR = 'mentor', _('Mentor')
        PARTNER = 'partner', _('Partner Organization')
        DONOR = 'donor', _('Donor')
        PUBLIC = 'public', _('Public User')

    class VerificationStatus(models.TextChoices):
        PENDING = 'pending', _('Pending Verification')
        VERIFIED = 'verified', _('Verified')
        REJECTED = 'rejected', _('Rejected')
        SUSPENDED = 'suspended', _('Suspended')

    # Core fields
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices,
        default=UserType.PUBLIC
    )
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING
    )
    
    # Profile information
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    alternate_email = models.EmailField(blank=True)
    profile_image = models.ImageField(
        upload_to='users/profile_images/%Y/%m/%d/',
        null=True,
        blank=True
    )
    bio = models.TextField(blank=True)
    
    # Professional information
    organization = models.CharField(max_length=255, blank=True)
    job_title = models.CharField(max_length=255, blank=True)
    expertise = models.JSONField(default=list, blank=True)
    education = models.JSONField(default=list, blank=True)  # List of education entries
    certifications = models.JSONField(default=list, blank=True)
    
    # Social links
    social_links = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON object with social media links"
    )
    
    # Location
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Preferences
    email_notifications = models.BooleanField(default=True)
    newsletter_subscription = models.BooleanField(default=False)
    language_preference = models.CharField(max_length=10, default='en')
    
    # Activity tracking
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    login_count = models.PositiveIntegerField(default=0)
    last_activity = models.DateTimeField(auto_now=True)
    
    # Metadata
    created_by = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_users'
    )
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    # Stats
    contribution_score = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        indexes = [
            models.Index(fields=['user_type']),
            models.Index(fields=['verification_status']),
            models.Index(fields=['country', 'city']),
        ]
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
    
    def get_full_profile(self):
        """Return comprehensive profile data"""
        return {
            'user': self,
            'stats': {
                'contributions': self.contribution_score,
                'login_count': self.login_count,
            }
        }


class UserActivityLog(models.Model):
    class ActivityType(models.TextChoices):
        LOGIN = 'login', _('Login')
        LOGOUT = 'logout', _('Logout')
        PROFILE_UPDATE = 'profile_update', _('Profile Update')
        PASSWORD_CHANGE = 'password_change', _('Password Change')
        CONTENT_CREATE = 'content_create', _('Content Creation')
        CONTENT_UPDATE = 'content_update', _('Content Update')
        CONTENT_DELETE = 'content_delete', _('Content Delete')
        APPLICATION_SUBMIT = 'application_submit', _('Application Submission')
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='activity_logs')
    activity_type = models.CharField(max_length=50, choices=ActivityType.choices)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'activity_type']),
            models.Index(fields=['timestamp']),
        ]


class UserVerification(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='verification')
    document_type = models.CharField(max_length=50)
    document_front = models.ImageField(upload_to='verification/documents/%Y/%m/%d/')
    document_back = models.ImageField(upload_to='verification/documents/%Y/%m/%d/', null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    verification_notes = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = 'User Verifications'