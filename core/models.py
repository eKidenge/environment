from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import uuid

User = get_user_model()

class SiteConfiguration(models.Model):
    """
    Central configuration for the YES website
    """
    site_name = models.CharField(max_length=255, default='Youth Environmental Scholars')
    tagline = models.CharField(max_length=500, blank=True)
    mission_statement = models.TextField()
    vision_statement = models.TextField()
    
    # Contact Information
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_address = models.TextField(blank=True)
    
    # Social Media Links
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    
    # Site Settings
    maintenance_mode = models.BooleanField(default=False)
    allow_registrations = models.BooleanField(default=True)
    allow_comments = models.BooleanField(default=True)
    
    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    meta_keywords = models.TextField(blank=True)
    
    # Analytics
    google_analytics_id = models.CharField(max_length=50, blank=True)
    facebook_pixel_id = models.CharField(max_length=50, blank=True)
    
    # File Upload Limits
    max_upload_size_mb = models.PositiveIntegerField(default=10)
    allowed_file_types = models.JSONField(
        default=list,
        blank=True,
        help_text="List of allowed file extensions"
    )
    
    # Email Configuration
    email_host = models.CharField(max_length=255, blank=True)
    email_port = models.PositiveIntegerField(default=587)
    email_use_tls = models.BooleanField(default=True)
    email_host_user = models.CharField(max_length=255, blank=True)
    email_host_password = models.CharField(max_length=255, blank=True)
    
    # Cache Settings
    cache_timeout = models.PositiveIntegerField(default=300)
    
    # Feature Flags
    enable_blog = models.BooleanField(default=True)
    enable_forum = models.BooleanField(default=False)
    enable_shop = models.BooleanField(default=False)
    enable_donations = models.BooleanField(default=True)
    
    # Theme Settings
    primary_color = models.CharField(max_length=7, default='#1a5fb4')
    secondary_color = models.CharField(max_length=7, default='#26a269')
    accent_color = models.CharField(max_length=7, default='#ff7800')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Site Configuration')
        verbose_name_plural = _('Site Configuration')
    
    def __str__(self):
        return f"{self.site_name} Configuration"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and SiteConfiguration.objects.exists():
            raise ValidationError('Only one SiteConfiguration instance can exist')
        return super().save(*args, **kwargs)


class TeamMember(models.Model):
    class MemberRole(models.TextChoices):
        DIRECTOR = 'director', _('Director')
        COORDINATOR = 'coordinator', _('Coordinator')
        MANAGER = 'manager', _('Manager')
        OFFICER = 'officer', _('Officer')
        ADVISOR = 'advisor', _('Advisor')
        VOLUNTEER = 'volunteer', _('Volunteer')
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='team_profile'
    )
    role = models.CharField(max_length=50, choices=MemberRole.choices)
    department = models.CharField(max_length=100, blank=True)
    bio = models.TextField()
    expertise = models.JSONField(default=list, blank=True)
    
    # Display settings
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_leadership = models.BooleanField(default=False)
    show_on_website = models.BooleanField(default=True)
    
    # Social media for team page
    team_twitter = models.URLField(blank=True)
    team_linkedin = models.URLField(blank=True)
    team_website = models.URLField(blank=True)
    
    # Stats
    years_with_yes = models.PositiveIntegerField(default=0)
    projects_led = models.PositiveIntegerField(default=0)
    
    # Media
    profile_image = models.ImageField(
        upload_to='team/profile_images/%Y/%m/%d/',
        null=True,
        blank=True
    )
    cover_image = models.ImageField(
        upload_to='team/cover_images/%Y/%m/%d/',
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', '-is_leadership', 'user__last_name']
        verbose_name = _('Team Member')
        verbose_name_plural = _('Team Members')
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"


class ImpactMetric(models.Model):
    class MetricType(models.TextChoices):
        ENVIRONMENTAL = 'environmental', _('Environmental')
        SOCIAL = 'social', _('Social')
        ECONOMIC = 'economic', _('Economic')
        EDUCATIONAL = 'educational', _('Educational')
        RESEARCH = 'research', _('Research')
    
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    metric_type = models.CharField(max_length=50, choices=MetricType.choices)
    description = models.TextField()
    unit = models.CharField(max_length=50)
    icon = models.CharField(max_length=100, blank=True)
    
    # Measurement
    current_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    target_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    baseline_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Calculation
    calculation_formula = models.TextField(blank=True)
    data_source = models.CharField(max_length=255, blank=True)
    update_frequency = models.CharField(max_length=50, blank=True)
    
    # Visualization
    chart_type = models.CharField(max_length=50, blank=True)
    display_color = models.CharField(max_length=7, default='#26a269')
    display_order = models.PositiveIntegerField(default=0)
    is_public = models.BooleanField(default=True)
    
    # History tracking
    history = models.JSONField(
        default=list,
        blank=True,
        help_text="Historical values with timestamps"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = _('Impact Metric')
        verbose_name_plural = _('Impact Metrics')
        indexes = [
            models.Index(fields=['metric_type', 'is_public']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.unit})"
    
    def calculate_progress(self):
        if self.target_value and self.baseline_value:
            total_range = self.target_value - self.baseline_value
            current_progress = self.current_value - self.baseline_value
            if total_range != 0:
                return (current_progress / total_range) * 100
        return 0


class FAQ(models.Model):
    class FAQCategory(models.TextChoices):
        GENERAL = 'general', _('General')
        MEMBERSHIP = 'membership', _('Membership')
        VOLUNTEERING = 'volunteering', _('Volunteering')
        DONATIONS = 'donations', _('Donations')
        PROGRAMS = 'programs', _('Programs')
        RESEARCH = 'research', _('Research')
        PARTNERSHIPS = 'partnerships', _('Partnerships')
        TECHNICAL = 'technical', _('Technical')
    
    question = models.TextField()
    answer = models.TextField()
    category = models.CharField(max_length=50, choices=FAQCategory.choices)
    slug = models.SlugField(max_length=255, unique=True)
    
    # Display settings
    display_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Stats
    views = models.PositiveIntegerField(default=0)
    helpful_yes = models.PositiveIntegerField(default=0)
    helpful_no = models.PositiveIntegerField(default=0)
    
    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    
    # Related
    related_faqs = models.ManyToManyField('self', blank=True, symmetrical=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_faqs'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_faqs'
    )
    
    class Meta:
        ordering = ['display_order', 'category', 'question']
        verbose_name = _('Frequently Asked Question')
        verbose_name_plural = _('Frequently Asked Questions')
        indexes = [
            models.Index(fields=['category', 'is_published']),
            models.Index(fields=['is_featured', 'is_published']),
        ]
    
    def __str__(self):
        return f"{self.question[:100]}..."


class SitePage(models.Model):
    class PageType(models.TextChoices):
        STATIC = 'static', _('Static Page')
        DYNAMIC = 'dynamic', _('Dynamic Page')
        LANDING = 'landing', _('Landing Page')
        FORM = 'form', _('Form Page')
    
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    page_type = models.CharField(max_length=50, choices=PageType.choices, default='static')
    
    # Content
    content = models.TextField(blank=True)
    excerpt = models.TextField(blank=True)
    
    # Media
    featured_image = models.ImageField(
        upload_to='pages/featured_images/%Y/%m/%d/',
        null=True,
        blank=True
    )
    
    # Settings
    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    show_in_navigation = models.BooleanField(default=False)
    navigation_order = models.PositiveIntegerField(default=0)
    require_authentication = models.BooleanField(default=False)
    
    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    meta_keywords = models.TextField(blank=True)
    canonical_url = models.URLField(blank=True)
    
    # Template
    template_name = models.CharField(max_length=100, blank=True)
    
    # Parent-child relationship
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    
    # Stats
    views = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_pages'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_pages'
    )
    
    class Meta:
        ordering = ['navigation_order', 'title']
        verbose_name = _('Site Page')
        verbose_name_plural = _('Site Pages')
        indexes = [
            models.Index(fields=['slug', 'is_published']),
            models.Index(fields=['show_in_navigation', 'is_published']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_breadcrumbs(self):
        """Generate breadcrumb trail for the page"""
        breadcrumbs = []
        current = self
        while current:
            breadcrumbs.insert(0, {
                'title': current.title,
                'slug': current.slug
            })
            current = current.parent
        return breadcrumbs


class NewsletterSubscription(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255, blank=True)
    
    # Preferences
    categories = models.JSONField(
        default=list,
        blank=True,
        help_text="Newsletter categories subscribed to"
    )
    frequency = models.CharField(
        max_length=50,
        choices=[
            ('weekly', 'Weekly'),
            ('biweekly', 'Bi-weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
        ],
        default='monthly'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    
    # Stats
    emails_sent = models.PositiveIntegerField(default=0)
    emails_opened = models.PositiveIntegerField(default=0)
    emails_clicked = models.PositiveIntegerField(default=0)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    subscribed_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    last_email_sent = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Newsletter Subscription')
        verbose_name_plural = _('Newsletter Subscriptions')
        indexes = [
            models.Index(fields=['email', 'is_active']),
            models.Index(fields=['is_active', 'is_verified']),
        ]
    
    def __str__(self):
        return self.email