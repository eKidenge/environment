from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()

class MentorshipProgram(models.Model):
    class ProgramType(models.TextChoices):
        ONE_ON_ONE = 'one_on_one', _('One-on-One Mentorship')
        GROUP = 'group', _('Group Mentorship')
        PEER = 'peer', _('Peer Mentorship')
        REVERSE = 'reverse', _('Reverse Mentorship')
        SPEED = 'speed', _('Speed Mentoring')
        PROJECT_BASED = 'project_based', _('Project-Based Mentoring')
    
    class ProgramStatus(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        UPCOMING = 'upcoming', _('Upcoming')
        ONGOING = 'ongoing', _('Ongoing')
        COMPLETED = 'completed', _('Completed')
        ARCHIVED = 'archived', _('Archived')
    
    # Basic Information
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    program_type = models.CharField(max_length=50, choices=ProgramType.choices)
    status = models.CharField(max_length=20, choices=ProgramStatus.choices, default='draft')
    
    # Description
    description = models.TextField()
    objectives = models.JSONField(default=list, blank=True)
    benefits = models.JSONField(default=list, blank=True)
    curriculum = models.TextField(blank=True)
    
    # Target Audience
    target_audience = models.JSONField(default=list, blank=True)
    prerequisites = models.TextField(blank=True)
    skills_focus = models.JSONField(default=list, blank=True)
    
    # Structure
    duration_weeks = models.PositiveIntegerField()
    time_commitment = models.CharField(max_length=100)  # e.g., "2-4 hours/week"
    format = models.CharField(max_length=100, choices=[
        ('virtual', 'Virtual'),
        ('in_person', 'In-Person'),
        ('hybrid', 'Hybrid'),
    ], default='virtual')
    
    # Capacity
    max_mentors = models.PositiveIntegerField(null=True, blank=True)
    max_mentees = models.PositiveIntegerField()
    current_mentors = models.PositiveIntegerField(default=0)
    current_mentees = models.PositiveIntegerField(default=0)
    
    # Timeline
    application_start = models.DateField()
    application_deadline = models.DateField()
    program_start = models.DateField()
    program_end = models.DateField()
    
    # Matching Criteria
    matching_criteria = models.JSONField(default=dict, blank=True)
    matching_algorithm = models.CharField(max_length=100, blank=True)
    allow_self_matching = models.BooleanField(default=False)
    
    # Team
    program_coordinator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                           related_name='coordinated_mentorship_programs')
    mentors = models.ManyToManyField(User, related_name='mentor_programs', blank=True)
    
    # Resources
    resources = models.JSONField(default=list, blank=True)
    toolkit = models.TextField(blank=True)
    
    # Evaluation
    success_metrics = models.JSONField(default=list, blank=True)
    evaluation_method = models.TextField(blank=True)
    
    # Media
    featured_image = models.ImageField(upload_to='mentorship/featured/%Y/%m/%d/', null=True, blank=True)
    
    # SEO & Display
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    
    # Statistics
    applications_count = models.PositiveIntegerField(default=0)
    matches_count = models.PositiveIntegerField(default=0)
    success_rate = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                  related_name='created_mentorship_programs')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug', 'status']),
            models.Index(fields=['program_type', 'status']),
            models.Index(fields=['is_featured', 'is_published']),
        ]
    
    def __str__(self):
        return self.title
    
    def is_accepting_applications(self):
        from django.utils import timezone
        today = timezone.now().date()
        return self.application_start <= today <= self.application_deadline


class MentorshipApplication(models.Model):
    class ApplicationStatus(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        SUBMITTED = 'submitted', _('Submitted')
        UNDER_REVIEW = 'under_review', _('Under Review')
        SHORTLISTED = 'shortlisted', _('Shortlisted')
        ACCEPTED = 'accepted', _('Accepted')
        REJECTED = 'rejected', _('Rejected')
        WITHDRAWN = 'withdrawn', _('Withdrawn')
    
    class RoleChoice(models.TextChoices):
        MENTOR = 'mentor', _('Mentor')
        MENTEE = 'mentee', _('Mentee')
        BOTH = 'both', _('Both (Mentor & Mentee)')
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    program = models.ForeignKey(MentorshipProgram, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentorship_applications')
    
    # Role Selection
    applying_as = models.CharField(max_length=20, choices=RoleChoice.choices)
    
    # Application Content
    motivation_statement = models.TextField()
    experience_summary = models.TextField()
    learning_goals = models.JSONField(default=list, blank=True)
    expertise_areas = models.JSONField(default=list, blank=True)
    availability = models.JSONField(default=dict, blank=True)
    
    # Documents
    resume = models.FileField(upload_to='mentorship/resumes/%Y/%m/%d/', null=True, blank=True)
    portfolio = models.URLField(blank=True)
    reference_letters = models.JSONField(default=list, blank=True)
    
    # Preferences
    preferences = models.JSONField(default=dict, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=ApplicationStatus.choices, default='draft')
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    # Review
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name='reviewed_mentorship_applications')
    review_notes = models.TextField(blank=True)
    review_score = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Interview
    interview_scheduled = models.DateTimeField(null=True, blank=True)
    interview_notes = models.TextField(blank=True)
    
    # Matching
    match_preferences = models.JSONField(default=dict, blank=True)
    match_score = models.FloatField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['program', 'applicant']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.applicant.username} - {self.program.title} ({self.get_applying_as_display()})"


class MentorshipMatch(models.Model):
    class MatchStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        PROPOSED = 'proposed', _('Proposed')
        ACCEPTED = 'accepted', _('Accepted')
        REJECTED = 'rejected', _('Rejected')
        ACTIVE = 'active', _('Active')
        COMPLETED = 'completed', _('Completed')
        TERMINATED = 'terminated', _('Terminated')
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    program = models.ForeignKey(MentorshipProgram, on_delete=models.CASCADE, related_name='matches')
    mentor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentor_matches')
    mentee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentee_matches')
    
    # Match Details
    match_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    match_reason = models.TextField(blank=True)
    compatibility_factors = models.JSONField(default=list, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=MatchStatus.choices, default='pending')
    proposed_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Agreement
    goals = models.JSONField(default=list, blank=True)
    meeting_frequency = models.CharField(max_length=100, blank=True)
    communication_channels = models.JSONField(default=list, blank=True)
    agreement_document = models.FileField(upload_to='mentorship/agreements/%Y/%m/%d/', null=True, blank=True)
    
    # Progress Tracking
    meetings_held = models.PositiveIntegerField(default=0)
    milestones_completed = models.PositiveIntegerField(default=0)
    progress_notes = models.TextField(blank=True)
    
    # Feedback
    mentor_feedback = models.TextField(blank=True)
    mentee_feedback = models.TextField(blank=True)
    overall_rating = models.FloatField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    matched_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                  related_name='created_matches')
    
    class Meta:
        unique_together = ['program', 'mentor', 'mentee']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.mentor.username} ↔ {self.mentee.username} - {self.program.title}"


class MentorshipSession(models.Model):
    class SessionStatus(models.TextChoices):
        SCHEDULED = 'scheduled', _('Scheduled')
        CONFIRMED = 'confirmed', _('Confirmed')
        IN_PROGRESS = 'in_progress', _('In Progress')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')
        RESCHEDULED = 'rescheduled', _('Rescheduled')
    
    match = models.ForeignKey(MentorshipMatch, on_delete=models.CASCADE, related_name='sessions')
    
    # Session Details
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    agenda = models.JSONField(default=list, blank=True)
    
    # Timing
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Location/Platform
    location_type = models.CharField(max_length=50, choices=[
        ('virtual', 'Virtual'),
        ('in_person', 'In-Person'),
        ('phone', 'Phone'),
    ], default='virtual')
    meeting_link = models.URLField(blank=True)
    location = models.JSONField(default=dict, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=SessionStatus.choices, default='scheduled')
    
    # Resources
    resources = models.JSONField(default=list, blank=True)
    
    # Notes
    preparation_notes = models.TextField(blank=True)
    session_notes = models.TextField(blank=True)
    action_items = models.JSONField(default=list, blank=True)
    
    # Feedback
    mentor_feedback = models.TextField(blank=True)
    mentee_feedback = models.TextField(blank=True)
    session_rating = models.FloatField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['scheduled_start']
    
    def __str__(self):
        return f"{self.title} - {self.match}"


class MentorshipResource(models.Model):
    class ResourceType(models.TextChoices):
        GUIDE = 'guide', _('Guide')
        TEMPLATE = 'template', _('Template')
        CHECKLIST = 'checklist', _('Checklist')
        VIDEO = 'video', _('Video')
        ARTICLE = 'article', _('Article')
        TOOL = 'tool', _('Tool')
        WORKSHEET = 'worksheet', _('Worksheet')
    
    program = models.ForeignKey(MentorshipProgram, on_delete=models.CASCADE, related_name='program_resources', 
                               null=True, blank=True)
    match = models.ForeignKey(MentorshipMatch, on_delete=models.CASCADE, related_name='match_resources', 
                             null=True, blank=True)
    
    resource_type = models.CharField(max_length=20, choices=ResourceType.choices)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Content
    file = models.FileField(upload_to='mentorship/resources/%Y/%m/%d/', null=True, blank=True)
    url = models.URLField(blank=True)
    content = models.TextField(blank=True)
    
    # Access
    access_level = models.CharField(max_length=50, choices=[
        ('public', 'Public'),
        ('program', 'Program Participants'),
        ('match', 'Match Specific'),
        ('private', 'Private'),
    ], default='program')
    
    # Metadata
    tags = models.JSONField(default=list, blank=True)
    download_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_resource_type_display()})"


class MentorshipFeedback(models.Model):
    class FeedbackType(models.TextChoices):
        SESSION = 'session', _('Session Feedback')
        PROGRAM = 'program', _('Program Feedback')
        MENTOR = 'mentor', _('Mentor Feedback')
        MENTEE = 'mentee', _('Mentee Feedback')
        GENERAL = 'general', _('General Feedback')
    
    feedback_type = models.CharField(max_length=20, choices=FeedbackType.choices)
    
    # Reference
    program = models.ForeignKey(MentorshipProgram, on_delete=models.CASCADE, null=True, blank=True)
    match = models.ForeignKey(MentorshipMatch, on_delete=models.CASCADE, null=True, blank=True)
    session = models.ForeignKey(MentorshipSession, on_delete=models.CASCADE, null=True, blank=True)
    
    # Feedback Provider
    provided_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_feedback')
    provided_for = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_feedback', 
                                    null=True, blank=True)
    
    # Ratings (1-5 scale)
    rating_knowledge = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    rating_communication = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    rating_support = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    rating_overall = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    # Qualitative Feedback
    strengths = models.TextField(blank=True)
    areas_for_improvement = models.TextField(blank=True)
    suggestions = models.TextField(blank=True)
    
    # Impact
    key_learnings = models.TextField(blank=True)
    application_plans = models.TextField(blank=True)
    would_recommend = models.BooleanField(default=True)
    
    # Status
    is_anonymous = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Feedback by {self.provided_by.username} ({self.get_feedback_type_display()})"


class MentorshipGoal(models.Model):
    class GoalStatus(models.TextChoices):
        NOT_STARTED = 'not_started', _('Not Started')
        IN_PROGRESS = 'in_progress', _('In Progress')
        COMPLETED = 'completed', _('Completed')
        ON_HOLD = 'on_hold', _('On Hold')
        ABANDONED = 'abandoned', _('Abandoned')
    
    match = models.ForeignKey(MentorshipMatch, on_delete=models.CASCADE, related_name='mentorship_goals')
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    # Planning
    category = models.CharField(max_length=100, blank=True)
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], default='medium')
    
    # Timeline
    target_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    
    # Progress
    status = models.CharField(max_length=20, choices=GoalStatus.choices, default='not_started')
    progress_percentage = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Metrics
    success_criteria = models.JSONField(default=list, blank=True)
    evidence = models.TextField(blank=True)
    
    # Review
    mentor_notes = models.TextField(blank=True)
    mentee_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['priority', 'target_date']
    
    def __str__(self):
        return f"{self.title} - {self.match}"