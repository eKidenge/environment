from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()

class VolunteerOpportunity(models.Model):
    class OpportunityType(models.TextChoices):
        VIRTUAL = 'virtual', _('Virtual')
        IN_PERSON = 'in_person', _('In-Person')
        HYBRID = 'hybrid', _('Hybrid')
    
    class OpportunityStatus(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        PUBLISHED = 'published', _('Published')
        ONGOING = 'ongoing', _('Ongoing')
        FILLED = 'filled', _('Filled')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')
        ARCHIVED = 'archived', _('Archived')
    
    class SkillLevel(models.TextChoices):
        BEGINNER = 'beginner', _('Beginner')
        INTERMEDIATE = 'intermediate', _('Intermediate')
        ADVANCED = 'advanced', _('Advanced')
        EXPERT = 'expert', _('Expert')
    
    # Basic Information
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    opportunity_type = models.CharField(max_length=20, choices=OpportunityType.choices)
    status = models.CharField(max_length=20, choices=OpportunityStatus.choices, default='draft')
    
    # Description
    description = models.TextField()
    responsibilities = models.JSONField(default=list, blank=True)
    impact_description = models.TextField(blank=True)
    learning_opportunities = models.JSONField(default=list, blank=True)
    
    # Requirements
    requirements = models.TextField(blank=True)
    skills_required = models.JSONField(default=list, blank=True)
    skills_preferred = models.JSONField(default=list, blank=True)
    skill_level = models.CharField(max_length=20, choices=SkillLevel.choices, default='beginner')
    
    # Logistics
    location = models.JSONField(default=dict, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    remote_allowed = models.BooleanField(default=False)
    
    # Time Commitment
    time_commitment = models.CharField(max_length=100)  # e.g., "5-10 hours/week"
    duration_weeks = models.PositiveIntegerField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    application_deadline = models.DateField(null=True, blank=True)
    
    # Capacity
    positions_available = models.PositiveIntegerField(default=1)
    positions_filled = models.PositiveIntegerField(default=0)
    min_age = models.PositiveIntegerField(null=True, blank=True)
    max_age = models.PositiveIntegerField(null=True, blank=True)
    
    # Team & Supervision
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name='supervised_opportunities')
    team_lead = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                 related_name='led_volunteer_opportunities')
    department = models.CharField(max_length=100, blank=True)
    
    # Related Programs/Projects
    related_programs = models.ManyToManyField('programs.Program', related_name='volunteer_opportunities', blank=True)
    related_projects = models.ManyToManyField('research.ResearchProject', related_name='volunteer_opportunities', blank=True)
    
    # Support & Benefits
    training_provided = models.BooleanField(default=False)
    training_description = models.TextField(blank=True)
    equipment_provided = models.BooleanField(default=False)
    equipment_description = models.TextField(blank=True)
    certification_provided = models.BooleanField(default=False)
    certificate_name = models.CharField(max_length=255, blank=True)
    
    # Safety & Compliance
    safety_requirements = models.TextField(blank=True)
    background_check_required = models.BooleanField(default=False)
    background_check_type = models.CharField(max_length=100, blank=True)
    liability_waiver_required = models.BooleanField(default=False)
    
    # Media
    featured_image = models.ImageField(upload_to='volunteer/opportunities/%Y/%m/%d/', null=True, blank=True)
    gallery = models.JSONField(default=list, blank=True)
    
    # SEO & Display
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    
    # Statistics
    views = models.PositiveIntegerField(default=0)
    applications_count = models.PositiveIntegerField(default=0)
    completion_rate = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    volunteer_satisfaction = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                  related_name='created_volunteer_opportunities')
    
    class Meta:
        verbose_name = _('Volunteer Opportunity')
        verbose_name_plural = _('Volunteer Opportunities')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug', 'status']),
            models.Index(fields=['opportunity_type', 'status']),
            models.Index(fields=['is_featured', 'is_published']),
            models.Index(fields=['city', 'country']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
    
    def is_accepting_applications(self):
        from django.utils import timezone
        today = timezone.now().date()
        if not self.is_published or self.status != 'published':
            return False
        if self.application_deadline and self.application_deadline < today:
            return False
        if self.positions_filled >= self.positions_available:
            return False
        return True
    
    def fill_percentage(self):
        if self.positions_available > 0:
            return (self.positions_filled / self.positions_available) * 100
        return 0


class VolunteerApplication(models.Model):
    class ApplicationStatus(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        SUBMITTED = 'submitted', _('Submitted')
        UNDER_REVIEW = 'under_review', _('Under Review')
        SHORTLISTED = 'shortlisted', _('Shortlisted')
        INTERVIEWING = 'interviewing', _('Interviewing')
        ACCEPTED = 'accepted', _('Accepted')
        REJECTED = 'rejected', _('Rejected')
        WITHDRAWN = 'withdrawn', _('Withdrawn')
        ON_HOLD = 'on_hold', _('On Hold')
    
    class AvailabilityType(models.TextChoices):
        FULL_TIME = 'full_time', _('Full Time')
        PART_TIME = 'part_time', _('Part Time')
        FLEXIBLE = 'flexible', _('Flexible')
        WEEKENDS = 'weekends', _('Weekends Only')
        EVENINGS = 'evenings', _('Evenings Only')
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    opportunity = models.ForeignKey(VolunteerOpportunity, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='volunteer_applications')
    
    # Application Details
    motivation_statement = models.TextField()
    relevant_experience = models.TextField()
    skills = models.JSONField(default=list, blank=True)
    availability_type = models.CharField(max_length=20, choices=AvailabilityType.choices, blank=True)
    hours_per_week = models.PositiveIntegerField(null=True, blank=True)
    start_date_preference = models.DateField(null=True, blank=True)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=255, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(max_length=100, blank=True)
    
    # Documents
    resume = models.FileField(upload_to='volunteer/resumes/%Y/%m/%d/', null=True, blank=True)
    cover_letter = models.FileField(upload_to='volunteer/cover_letters/%Y/%m/%d/', null=True, blank=True)
    portfolio = models.URLField(blank=True)
    additional_docs = models.JSONField(default=list, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=ApplicationStatus.choices, default='draft')
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    # Review Process
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name='reviewed_volunteer_applications')
    review_notes = models.TextField(blank=True)
    review_score = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Interview
    interview_scheduled = models.DateTimeField(null=True, blank=True)
    interview_notes = models.TextField(blank=True)
    interview_score = models.FloatField(null=True, blank=True)
    
    # Background Check
    background_check_status = models.CharField(max_length=50, blank=True, choices=[
        ('not_required', 'Not Required'),
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='not_required')
    background_check_completed_at = models.DateTimeField(null=True, blank=True)
    
    # Training
    training_status = models.CharField(max_length=50, blank=True, choices=[
        ('not_started', 'Not Started'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='not_started')
    training_completed_at = models.DateTimeField(null=True, blank=True)
    
    # Onboarding
    onboarding_status = models.CharField(max_length=50, blank=True, choices=[
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ], default='not_started')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['opportunity', 'applicant']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.applicant.username} - {self.opportunity.title}"


class VolunteerAssignment(models.Model):
    class AssignmentStatus(models.TextChoices):
        PENDING = 'pending', _('Pending Start')
        ACTIVE = 'active', _('Active')
        ON_LEAVE = 'on_leave', _('On Leave')
        COMPLETED = 'completed', _('Completed')
        TERMINATED = 'terminated', _('Terminated')
        EXTENDED = 'extended', _('Extended')
    
    application = models.OneToOneField(VolunteerApplication, on_delete=models.CASCADE, related_name='assignment')
    
    # Assignment Details
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    expected_hours_per_week = models.PositiveIntegerField()
    work_schedule = models.JSONField(default=dict, blank=True)
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                  related_name='supervised_volunteers')
    team_members = models.ManyToManyField(User, related_name='volunteer_teams', blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=AssignmentStatus.choices, default='pending')
    actual_start_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)
    
    # Performance Tracking
    hours_logged = models.PositiveIntegerField(default=0)
    tasks_completed = models.PositiveIntegerField(default=0)
    performance_rating = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(5)])
    performance_notes = models.TextField(blank=True)
    
    # Resources
    equipment_assigned = models.JSONField(default=list, blank=True)
    access_provided = models.JSONField(default=list, blank=True)
    
    # Certificates & Recognition
    certificate_issued = models.BooleanField(default=False)
    certificate_serial = models.CharField(max_length=100, blank=True)
    issued_at = models.DateTimeField(null=True, blank=True)
    recognition_awards = models.JSONField(default=list, blank=True)
    
    # Feedback
    volunteer_feedback = models.TextField(blank=True)
    supervisor_feedback = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Assignment: {self.application.applicant.username} - {self.application.opportunity.title}"


class VolunteerTimeLog(models.Model):
    class LogStatus(models.TextChoices):
        PENDING = 'pending', _('Pending Approval')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')
        ADJUSTED = 'adjusted', _('Adjusted')
    
    assignment = models.ForeignKey(VolunteerAssignment, on_delete=models.CASCADE, related_name='time_logs')
    volunteer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='volunteer_time_logs')
    
    # Time Details
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    total_hours = models.FloatField()
    break_duration = models.FloatField(default=0)  # in hours
    
    # Activity Details
    activity_description = models.TextField()
    tasks_completed = models.JSONField(default=list, blank=True)
    project = models.CharField(max_length=255, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=LogStatus.choices, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='approved_time_logs')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Location
    location = models.JSONField(default=dict, blank=True)
    remote_work = models.BooleanField(default=False)
    
    # Notes
    notes = models.TextField(blank=True)
    challenges_faced = models.TextField(blank=True)
    achievements = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"Time Log: {self.volunteer.username} - {self.date} ({self.total_hours} hours)"


class VolunteerSkill(models.Model):
    """Track volunteer skills for matching"""
    volunteer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='volunteer_skills')
    skill_name = models.CharField(max_length=100)
    skill_level = models.CharField(max_length=20, choices=VolunteerOpportunity.SkillLevel.choices)
    years_experience = models.PositiveIntegerField(default=0)
    certification = models.CharField(max_length=255, blank=True)
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Usage
    times_utilized = models.PositiveIntegerField(default=0)
    last_used = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['volunteer', 'skill_name']
    
    def __str__(self):
        return f"{self.volunteer.username} - {self.skill_name} ({self.get_skill_level_display()})"


class VolunteerAward(models.Model):
    class AwardType(models.TextChoices):
        CERTIFICATE = 'certificate', _('Certificate of Appreciation')
        BADGE = 'badge', _('Digital Badge')
        LETTER = 'letter', _('Recommendation Letter')
        PHYSICAL = 'physical', _('Physical Award')
        SCHOLARSHIP = 'scholarship', _('Scholarship')
        OTHER = 'other', _('Other Recognition')
    
    volunteer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='volunteer_awards')
    award_type = models.CharField(max_length=20, choices=AwardType.choices)
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    # Details
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='issued_awards')
    issued_at = models.DateTimeField()
    valid_until = models.DateField(null=True, blank=True)
    
    # Media
    certificate_file = models.FileField(upload_to='volunteer/awards/%Y/%m/%d/', null=True, blank=True)
    badge_image = models.ImageField(upload_to='volunteer/badges/%Y/%m/%d/', null=True, blank=True)
    badge_url = models.URLField(blank=True)
    
    # Verification
    verification_code = models.CharField(max_length=100, blank=True)
    is_public = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-issued_at']
    
    def __str__(self):
        return f"{self.title} - {self.volunteer.username}"


class VolunteerEvent(models.Model):
    """Events for volunteers (training, appreciation, etc.)"""
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    
    # Event Details
    description = models.TextField()
    event_type = models.CharField(max_length=50, choices=[
        ('training', 'Training'),
        ('orientation', 'Orientation'),
        ('appreciation', 'Appreciation Event'),
        ('networking', 'Networking'),
        ('workshop', 'Workshop'),
        ('social', 'Social Gathering'),
        ('meeting', 'Team Meeting'),
    ])
    
    # Timing
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Location
    location_type = models.CharField(max_length=50, choices=[
        ('virtual', 'Virtual'),
        ('in_person', 'In-Person'),
        ('hybrid', 'Hybrid'),
    ], default='virtual')
    location = models.JSONField(default=dict, blank=True)
    online_link = models.URLField(blank=True)
    
    # Audience
    target_audience = models.JSONField(default=list, blank=True)
    max_attendees = models.PositiveIntegerField(null=True, blank=True)
    current_attendees = models.PositiveIntegerField(default=0)
    
    # Registration
    registration_required = models.BooleanField(default=True)
    registration_deadline = models.DateTimeField(null=True, blank=True)
    
    # Presenters/Organizers
    organizers = models.ManyToManyField(User, related_name='organized_volunteer_events', blank=True)
    presenters = models.ManyToManyField(User, related_name='presented_volunteer_events', blank=True)
    
    # Resources
    resources = models.JSONField(default=list, blank=True)
    agenda = models.JSONField(default=list, blank=True)
    
    # Status
    is_published = models.BooleanField(default=True)
    is_cancelled = models.BooleanField(default=False)
    
    # Statistics
    attendance_rate = models.FloatField(default=0)
    satisfaction_rating = models.FloatField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['start_datetime']
    
    def __str__(self):
        return self.title