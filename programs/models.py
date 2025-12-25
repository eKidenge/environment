from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

User = get_user_model()

class ProgramCategory(models.Model):
    """Categories for programs (Climate Action, Conservation, etc.)"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, default='#1a5fb4')
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _('Program Category')
        verbose_name_plural = _('Program Categories')
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name


class Program(models.Model):
    class ProgramStatus(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        UPCOMING = 'upcoming', _('Upcoming')
        ONGOING = 'ongoing', _('Ongoing')
        COMPLETED = 'completed', _('Completed')
        ARCHIVED = 'archived', _('Archived')
    
    class ProgramType(models.TextChoices):
        RESEARCH = 'research', _('Research')
        COMMUNITY = 'community', _('Community Engagement')
        EDUCATION = 'education', _('Education')
        ADVOCACY = 'advocacy', _('Advocacy')
        INNOVATION = 'innovation', _('Innovation')
        CONSERVATION = 'conservation', _('Conservation')
        CAPACITY_BUILDING = 'capacity_building', _('Capacity Building')
    
    # Basic Information
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    category = models.ForeignKey(ProgramCategory, on_delete=models.PROTECT, related_name='programs')
    program_type = models.CharField(max_length=50, choices=ProgramType.choices)
    status = models.CharField(max_length=20, choices=ProgramStatus.choices, default='draft')
    
    # Description
    short_description = models.TextField()
    full_description = models.TextField()
    objectives = models.JSONField(default=list, blank=True)
    target_audience = models.JSONField(default=list, blank=True)
    
    # Media
    featured_image = models.ImageField(upload_to='programs/featured/%Y/%m/%d/')
    gallery = models.JSONField(default=list, blank=True)
    video_url = models.URLField(blank=True)
    
    # Timeline
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    application_deadline = models.DateField(null=True, blank=True)
    
    # Location
    location_type = models.CharField(max_length=50, choices=[
        ('onsite', 'On-site'),
        ('online', 'Online'),
        ('hybrid', 'Hybrid'),
    ], default='onsite')
    location = models.JSONField(default=dict, blank=True)
    online_link = models.URLField(blank=True)
    
    # Capacity
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    min_participants = models.PositiveIntegerField(default=1)
    current_participants = models.PositiveIntegerField(default=0)
    
    # Requirements
    eligibility_criteria = models.TextField(blank=True)
    required_documents = models.JSONField(default=list, blank=True)
    skills_required = models.JSONField(default=list, blank=True)
    
    # Financial
    is_free = models.BooleanField(default=True)
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fee_currency = models.CharField(max_length=3, default='USD')
    scholarships_available = models.BooleanField(default=False)
    funding_partners = models.ManyToManyField('partners.PartnerOrganization', blank=True)
    
    # Impact Metrics
    impact_metrics = models.JSONField(default=dict, blank=True)
    success_stories = models.JSONField(default=list, blank=True)
    
    # Team
    program_lead = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='led_programs')
    coordinators = models.ManyToManyField(User, related_name='coordinated_programs', blank=True)
    mentors = models.ManyToManyField(User, related_name='mentored_programs', blank=True)
    partners = models.ManyToManyField('partners.PartnerOrganization', related_name='partnered_programs', blank=True)
    
    # SEO & Display
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    views = models.PositiveIntegerField(default=0)
    applications_count = models.PositiveIntegerField(default=0)
    completion_rate = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_programs')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug', 'status']),
            models.Index(fields=['program_type', 'status']),
            models.Index(fields=['is_featured', 'is_published']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)


class ProgramApplication(models.Model):
    class ApplicationStatus(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        SUBMITTED = 'submitted', _('Submitted')
        UNDER_REVIEW = 'under_review', _('Under Review')
        SHORTLISTED = 'shortlisted', _('Shortlisted')
        ACCEPTED = 'accepted', _('Accepted')
        REJECTED = 'rejected', _('Rejected')
        WITHDRAWN = 'withdrawn', _('Withdrawn')
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='program_applications')
    
    # Application Data
    motivation_statement = models.TextField()
    relevant_experience = models.TextField()
    skills = models.JSONField(default=list, blank=True)
    learning_objectives = models.TextField(blank=True)
    
    # Documents
    resume = models.FileField(upload_to='applications/resumes/%Y/%m/%d/', null=True, blank=True)
    portfolio = models.URLField(blank=True)
    additional_docs = models.JSONField(default=list, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=ApplicationStatus.choices, default='draft')
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    # Review
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_applications')
    review_notes = models.TextField(blank=True)
    review_score = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Interview
    interview_scheduled = models.DateTimeField(null=True, blank=True)
    interview_notes = models.TextField(blank=True)
    interview_score = models.FloatField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['program', 'applicant']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.applicant.username} - {self.program.title}"


class ProgramUpdate(models.Model):
    """Updates/news about a program"""
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='updates')
    title = models.CharField(max_length=255)
    content = models.TextField()
    
    # Media
    images = models.JSONField(default=list, blank=True)
    documents = models.JSONField(default=list, blank=True)
    
    # Metadata
    is_important = models.BooleanField(default=False)
    send_notification = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.program.title} - {self.title}"


class ProgramResource(models.Model):
    class ResourceType(models.TextChoices):
        DOCUMENT = 'document', _('Document')
        VIDEO = 'video', _('Video')
        LINK = 'link', _('Link')
        TOOL = 'tool', _('Tool')
        DATASET = 'dataset', _('Dataset')
    
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='resources')
    resource_type = models.CharField(max_length=20, choices=ResourceType.choices)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Content based on type
    file = models.FileField(upload_to='programs/resources/%Y/%m/%d/', null=True, blank=True)
    url = models.URLField(blank=True)
    embed_code = models.TextField(blank=True)
    
    # Access control
    is_public = models.BooleanField(default=True)
    access_level = models.CharField(max_length=50, choices=[
        ('all', 'All Participants'),
        ('accepted', 'Accepted Participants Only'),
        ('team', 'Program Team Only'),
    ], default='all')
    
    # Metadata
    download_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_resource_type_display()})"


class ProgramParticipant(models.Model):
    class ParticipantStatus(models.TextChoices):
        ACTIVE = 'active', _('Active')
        COMPLETED = 'completed', _('Completed')
        DROPPED = 'dropped', _('Dropped Out')
        SUSPENDED = 'suspended', _('Suspended')
    
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='program_participations')
    application = models.OneToOneField(ProgramApplication, on_delete=models.CASCADE, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=ParticipantStatus.choices, default='active')
    joined_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Performance
    attendance_rate = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    performance_score = models.FloatField(null=True, blank=True)
    certificate_issued = models.BooleanField(default=False)
    certificate_serial = models.CharField(max_length=100, blank=True)
    
    # Feedback
    feedback_given = models.BooleanField(default=False)
    feedback_rating = models.FloatField(null=True, blank=True)
    feedback_notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['program', 'user']
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.program.title}"


class ProgramEvent(models.Model):
    """Individual events within a program (workshops, seminars, etc.)"""
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    # Timing
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Location
    location_type = models.CharField(max_length=50, choices=[
        ('physical', 'Physical'),
        ('online', 'Online'),
        ('hybrid', 'Hybrid'),
    ], default='physical')
    location = models.JSONField(default=dict, blank=True)
    online_link = models.URLField(blank=True)
    
    # Presenters
    presenters = models.ManyToManyField(User, related_name='presented_events', blank=True)
    
    # Resources
    resources = models.ManyToManyField(ProgramResource, blank=True)
    
    # Registration
    registration_required = models.BooleanField(default=False)
    max_attendees = models.PositiveIntegerField(null=True, blank=True)
    current_attendees = models.PositiveIntegerField(default=0)
    
    # Status
    is_published = models.BooleanField(default=True)
    is_cancelled = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['start_datetime']
    
    def __str__(self):
        return f"{self.title} - {self.program.title}"