from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()

class PartnerOrganization(models.Model):
    class OrganizationType(models.TextChoices):
        CORPORATE = 'corporate', _('Corporate')
        NGO = 'ngo', _('Non-Governmental Organization')
        GOVERNMENT = 'government', _('Government Agency')
        ACADEMIC = 'academic', _('Academic Institution')
        RESEARCH = 'research', _('Research Institute')
        MEDIA = 'media', _('Media Organization')
        COMMUNITY = 'community', _('Community Organization')
        FOUNDATION = 'foundation', _('Foundation')
        STARTUP = 'startup', _('Startup')
        INDIVIDUAL = 'individual', _('Individual Donor')
    
    class PartnershipLevel(models.TextChoices):
        STRATEGIC = 'strategic', _('Strategic Partner')
        MAJOR = 'major', _('Major Partner')
        SUPPORTING = 'supporting', _('Supporting Partner')
        COMMUNITY = 'community', _('Community Partner')
        IN_KIND = 'in_kind', _('In-Kind Partner')
        EVENT = 'event', _('Event Partner')
        MEDIA = 'media', _('Media Partner')
    
    class PartnershipStatus(models.TextChoices):
        PROSPECT = 'prospect', _('Prospect')
        IN_DISCUSSION = 'in_discussion', _('In Discussion')
        AGREEMENT_PENDING = 'agreement_pending', _('Agreement Pending')
        ACTIVE = 'active', _('Active')
        RENEWAL_PENDING = 'renewal_pending', _('Renewal Pending')
        INACTIVE = 'inactive', _('Inactive')
        TERMINATED = 'terminated', _('Terminated')
        ARCHIVED = 'archived', _('Archived')
    
    # Basic Information
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    organization_type = models.CharField(max_length=50, choices=OrganizationType.choices)
    partnership_level = models.CharField(max_length=50, choices=PartnershipLevel.choices, default='supporting')
    status = models.CharField(max_length=50, choices=PartnershipStatus.choices, default='prospect')
    
    # Organization Details
    description = models.TextField()
    mission = models.TextField(blank=True)
    vision = models.TextField(blank=True)
    values = models.JSONField(default=list, blank=True)
    focus_areas = models.JSONField(default=list, blank=True)
    
    # Contact Information
    website = models.URLField()
    primary_email = models.EmailField()
    primary_phone = models.CharField(max_length=20, blank=True)
    secondary_email = models.EmailField(blank=True)
    secondary_phone = models.CharField(max_length=20, blank=True)
    
    # Location
    headquarters = models.JSONField(default=dict, blank=True)
    country = models.CharField(max_length=100)
    region = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    operating_countries = models.JSONField(default=list, blank=True)
    
    # Organization Stats
    founded_year = models.PositiveIntegerField(null=True, blank=True)
    employee_count = models.CharField(max_length=50, blank=True)  # e.g., "50-100", "1000+"
    annual_budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    budget_currency = models.CharField(max_length=3, default='USD')
    
    # Key People
    contact_person = models.CharField(max_length=255)
    contact_position = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)
    
    focal_point = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='partner_focal_points')
    decision_maker = models.CharField(max_length=255, blank=True)
    decision_maker_position = models.CharField(max_length=255, blank=True)
    
    # Media
    logo = models.ImageField(upload_to='partners/logos/%Y/%m/%d/')
    logo_white = models.ImageField(upload_to='partners/logos/white/%Y/%m/%d/', null=True, blank=True)
    cover_image = models.ImageField(upload_to='partners/covers/%Y/%m/%d/', null=True, blank=True)
    brand_assets = models.JSONField(default=list, blank=True)
    
    # Partnership Details
    partnership_start = models.DateField(null=True, blank=True)
    partnership_end = models.DateField(null=True, blank=True)
    agreement_document = models.FileField(upload_to='partners/agreements/%Y/%m/%d/', null=True, blank=True)
    agreement_version = models.CharField(max_length=50, blank=True)
    agreement_status = models.CharField(max_length=50, choices=[
        ('draft', 'Draft'),
        ('under_review', 'Under Review'),
        ('signed', 'Signed'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
    ], default='draft')
    
    # Collaboration Areas
    collaboration_areas = models.JSONField(default=list, blank=True)
    joint_projects = models.JSONField(default=list, blank=True)
    expertise_shared = models.JSONField(default=list, blank=True)
    resources_shared = models.JSONField(default=list, blank=True)
    
    # Financial Contributions
    total_funding = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    funding_currency = models.CharField(max_length=3, default='USD')
    funding_breakdown = models.JSONField(default=list, blank=True)
    in_kind_contributions = models.TextField(blank=True)
    in_kind_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Impact & Metrics
    projects_supported = models.PositiveIntegerField(default=0)
    people_reached = models.PositiveIntegerField(default=0)
    impact_stories = models.JSONField(default=list, blank=True)
    success_metrics = models.JSONField(default=dict, blank=True)
    
    # Communication & Reporting
    communication_frequency = models.CharField(max_length=50, blank=True)
    last_communication = models.DateField(null=True, blank=True)
    next_communication = models.DateField(null=True, blank=True)
    reporting_requirements = models.TextField(blank=True)
    report_frequency = models.CharField(max_length=50, blank=True)
    
    # Strategic Alignment
    sdg_alignment = models.JSONField(default=list, blank=True)  # UN Sustainable Development Goals
    strategic_fit = models.TextField(blank=True)
    risk_assessment = models.TextField(blank=True)
    risk_level = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], default='low')
    
    # Social Media & Online Presence
    social_media = models.JSONField(default=dict, blank=True)
    press_mentions = models.JSONField(default=list, blank=True)
    publications = models.JSONField(default=list, blank=True)
    
    # Internal Notes & Evaluation
    internal_notes = models.TextField(blank=True)
    strengths = models.TextField(blank=True)
    weaknesses = models.TextField(blank=True)
    opportunities = models.TextField(blank=True)
    threats = models.TextField(blank=True)
    partner_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Visibility & Display
    is_featured = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    show_on_website = models.BooleanField(default=True)
    
    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='verified_partners')
    
    class Meta:
        ordering = ['display_order', '-partnership_start', 'name']
        indexes = [
            models.Index(fields=['slug', 'status']),
            models.Index(fields=['organization_type', 'partnership_level']),
            models.Index(fields=['country', 'city']),
            models.Index(fields=['is_featured', 'is_public']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_organization_type_display()})"
    
    def partnership_duration(self):
        """Calculate partnership duration in years"""
        if self.partnership_start and self.partnership_end:
            delta = self.partnership_end - self.partnership_start
            return delta.days // 365
        elif self.partnership_start:
            delta = timezone.now().date() - self.partnership_start
            return delta.days // 365
        return 0
    
    def total_contribution_value(self):
        """Calculate total contribution value (cash + in-kind)"""
        return self.total_funding + self.in_kind_value
    
    def is_active_partnership(self):
        """Check if partnership is currently active"""
        today = timezone.now().date()
        if self.status != 'active':
            return False
        if self.partnership_end and self.partnership_end < today:
            return False
        return True


class PartnershipAgreement(models.Model):
    """Detailed partnership agreements"""
    partner = models.ForeignKey(PartnerOrganization, on_delete=models.CASCADE, related_name='agreements')
    
    # Agreement Details
    agreement_title = models.CharField(max_length=255)
    agreement_number = models.CharField(max_length=100, unique=True)
    version = models.CharField(max_length=20, default='1.0')
    
    # Content
    purpose = models.TextField()
    objectives = models.JSONField(default=list, blank=True)
    scope = models.TextField()
    deliverables = models.JSONField(default=list, blank=True)
    responsibilities = models.JSONField(default=dict, blank=True)
    
    # Terms
    effective_date = models.DateField()
    expiration_date = models.DateField(null=True, blank=True)
    renewal_terms = models.TextField(blank=True)
    termination_clause = models.TextField(blank=True)
    
    # Financial Terms
    financial_commitment = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    payment_schedule = models.JSONField(default=list, blank=True)
    in_kind_commitments = models.TextField(blank=True)
    
    # Legal
    governing_law = models.CharField(max_length=100, blank=True)
    jurisdiction = models.CharField(max_length=100, blank=True)
    confidentiality = models.BooleanField(default=True)
    intellectual_property = models.TextField(blank=True)
    
    # Documents
    agreement_document = models.FileField(upload_to='partners/agreement_docs/%Y/%m/%d/')
    annexes = models.JSONField(default=list, blank=True)
    amendments = models.JSONField(default=list, blank=True)
    
    # Signatories
    our_signatory = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                     related_name='signed_agreements_our')
    partner_signatory_name = models.CharField(max_length=255)
    partner_signatory_position = models.CharField(max_length=255)
    signed_date = models.DateField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=50, choices=[
        ('draft', 'Draft'),
        ('under_review', 'Under Review'),
        ('ready_for_signature', 'Ready for Signature'),
        ('signed', 'Signed'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
        ('archived', 'Archived'),
    ], default='draft')
    
    # Compliance
    compliance_status = models.CharField(max_length=50, blank=True)
    compliance_notes = models.TextField(blank=True)
    last_review_date = models.DateField(null=True, blank=True)
    next_review_date = models.DateField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                  related_name='created_agreements')
    
    class Meta:
        ordering = ['-effective_date', '-created_at']
    
    def __str__(self):
        return f"{self.agreement_number}: {self.partner.name}"


class PartnershipProject(models.Model):
    """Joint projects with partners"""
    partner = models.ForeignKey(PartnerOrganization, on_delete=models.CASCADE, related_name='projects')
    program = models.ForeignKey('programs.Program', on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name='partnership_projects')
    research_project = models.ForeignKey('research.ResearchProject', on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='partnership_projects')
    
    # Project Details
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField()
    objectives = models.JSONField(default=list, blank=True)
    
    # Scope
    geographic_scope = models.JSONField(default=dict, blank=True)
    thematic_areas = models.JSONField(default=list, blank=True)
    target_audience = models.JSONField(default=list, blank=True)
    
    # Timeline
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=[
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('completed', 'Completed'),
        ('evaluation', 'Under Evaluation'),
        ('archived', 'Archived'),
    ], default='planning')
    
    # Resources
    budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    partner_contribution = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    yes_contribution = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    in_kind_contributions = models.TextField(blank=True)
    
    # Team
    project_lead = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                    related_name='led_partnership_projects')
    partner_lead = models.CharField(max_length=255, blank=True)
    team_members = models.ManyToManyField(User, related_name='partnership_project_teams', blank=True)
    
    # Deliverables
    deliverables = models.JSONField(default=list, blank=True)
    milestones = models.JSONField(default=list, blank=True)
    
    # Impact
    expected_impact = models.TextField(blank=True)
    success_metrics = models.JSONField(default=dict, blank=True)
    actual_results = models.TextField(blank=True)
    
    # Media
    featured_image = models.ImageField(upload_to='partnerships/projects/%Y/%m/%d/', null=True, blank=True)
    gallery = models.JSONField(default=list, blank=True)
    case_study = models.FileField(upload_to='partnerships/case_studies/%Y/%m/%d/', null=True, blank=True)
    
    # Communication
    communication_plan = models.TextField(blank=True)
    reporting_requirements = models.TextField(blank=True)
    
    # Evaluation
    lessons_learned = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    sustainability_plan = models.TextField(blank=True)
    
    # Visibility
    is_featured = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-start_date', '-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.partner.name}"


class PartnerContact(models.Model):
    """Contacts at partner organizations"""
    partner = models.ForeignKey(PartnerOrganization, on_delete=models.CASCADE, related_name='contacts')
    
    # Contact Details
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    position = models.CharField(max_length=255)
    department = models.CharField(max_length=100, blank=True)
    
    # Contact Information
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    mobile = models.CharField(max_length=20, blank=True)
    whatsapp = models.CharField(max_length=20, blank=True)
    
    # Communication Preferences
    preferred_contact_method = models.CharField(max_length=50, choices=[
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('whatsapp', 'WhatsApp'),
        ('in_person', 'In Person'),
    ], default='email')
    preferred_contact_time = models.CharField(max_length=100, blank=True)
    language_preference = models.CharField(max_length=50, default='English')
    
    # Role in Partnership
    role = models.CharField(max_length=100, blank=True)
    decision_making_level = models.CharField(max_length=50, choices=[
        ('none', 'No Decision Making'),
        ('influencer', 'Influencer'),
        ('recommender', 'Recommender'),
        ('approver', 'Approver'),
        ('decision_maker', 'Decision Maker'),
    ], default='influencer')
    
    # Relationship Management
    relationship_strength = models.IntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)])
    last_contact = models.DateField(null=True, blank=True)
    next_contact = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    # Social Media
    linkedin = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-is_primary', 'last_name', 'first_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.partner.name}"
    
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class PartnershipMeeting(models.Model):
    """Meetings with partners"""
    partner = models.ForeignKey(PartnerOrganization, on_delete=models.CASCADE, related_name='meetings')
    project = models.ForeignKey(PartnershipProject, on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name='meetings')
    
    # Meeting Details
    title = models.CharField(max_length=255)
    purpose = models.TextField()
    agenda = models.JSONField(default=list, blank=True)
    
    # Timing
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Location/Platform
    meeting_type = models.CharField(max_length=50, choices=[
        ('in_person', 'In Person'),
        ('virtual', 'Virtual'),
        ('hybrid', 'Hybrid'),
    ], default='virtual')
    location = models.JSONField(default=dict, blank=True)
    meeting_link = models.URLField(blank=True)
    dial_in_info = models.TextField(blank=True)
    
    # Participants
    yes_team = models.ManyToManyField(User, related_name='partner_meetings_yes', blank=True)
    partner_team = models.JSONField(default=list, blank=True)
    
    # Status
    status = models.CharField(max_length=50, choices=[
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
    ], default='scheduled')
    
    # Follow-up
    decisions_made = models.JSONField(default=list, blank=True)
    action_items = models.JSONField(default=list, blank=True)
    next_steps = models.TextField(blank=True)
    meeting_notes = models.TextField(blank=True)
    minutes_document = models.FileField(upload_to='partners/meeting_minutes/%Y/%m/%d/', null=True, blank=True)
    
    # Feedback
    satisfaction_rating = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(5)])
    feedback = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-scheduled_date', '-scheduled_time']
    
    def __str__(self):
        return f"{self.title} - {self.partner.name}"


class PartnershipResource(models.Model):
    """Resources shared with or from partners"""
    class ResourceType(models.TextChoices):
        DOCUMENT = 'document', _('Document')
        TEMPLATE = 'template', _('Template')
        TOOL = 'tool', _('Tool')
        DATA = 'data', _('Data Set')
        REPORT = 'report', _('Report')
        PRESENTATION = 'presentation', _('Presentation')
        MEDIA = 'media', _('Media File')
        OTHER = 'other', _('Other')
    
    class ResourceDirection(models.TextChoices):
        TO_PARTNER = 'to_partner', _('Shared with Partner')
        FROM_PARTNER = 'from_partner', _('Received from Partner')
        SHARED = 'shared', _('Mutually Shared')
    
    partner = models.ForeignKey(PartnerOrganization, on_delete=models.CASCADE, related_name='resources')
    project = models.ForeignKey(PartnershipProject, on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name='resources')
    
    # Resource Details
    resource_type = models.CharField(max_length=50, choices=ResourceType.choices)
    direction = models.CharField(max_length=50, choices=ResourceDirection.choices, default='shared')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Content
    file = models.FileField(upload_to='partners/resources/%Y/%m/%d/', null=True, blank=True)
    url = models.URLField(blank=True)
    
    # Metadata
    version = models.CharField(max_length=50, blank=True)
    language = models.CharField(max_length=50, default='English')
    tags = models.JSONField(default=list, blank=True)
    
    # Access & Usage
    confidentiality_level = models.CharField(max_length=50, choices=[
        ('public', 'Public'),
        ('internal', 'Internal Use Only'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted'),
    ], default='internal')
    usage_terms = models.TextField(blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    
    # Statistics
    download_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.partner.name}"


class PartnerEvaluation(models.Model):
    """Evaluations of partners"""
    partner = models.ForeignKey(PartnerOrganization, on_delete=models.CASCADE, related_name='evaluations')
    evaluated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='partner_evaluations')
    
    # Evaluation Period
    evaluation_period_start = models.DateField()
    evaluation_period_end = models.DateField()
    evaluation_date = models.DateField()
    
    # Ratings (1-5 scale)
    rating_strategic_alignment = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    rating_communication = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    rating_reliability = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    rating_value_added = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    rating_innovation = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    rating_overall = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    # Qualitative Assessment
    strengths = models.TextField()
    areas_for_improvement = models.TextField()
    key_achievements = models.JSONField(default=list, blank=True)
    challenges_faced = models.TextField(blank=True)
    
    # Recommendations
    continue_partnership = models.BooleanField(default=True)
    partnership_level_recommendation = models.CharField(max_length=50, choices=PartnerOrganization.PartnershipLevel.choices, blank=True)
    specific_recommendations = models.TextField()
    
    # Impact Assessment
    impact_on_yes = models.TextField(blank=True)
    impact_on_partner = models.TextField(blank=True)
    mutual_benefits = models.TextField(blank=True)
    
    # Documents
    evaluation_report = models.FileField(upload_to='partners/evaluations/%Y/%m/%d/', null=True, blank=True)
    supporting_documents = models.JSONField(default=list, blank=True)
    
    # Status
    is_finalized = models.BooleanField(default=False)
    finalized_at = models.DateTimeField(null=True, blank=True)
    shared_with_partner = models.BooleanField(default=False)
    shared_date = models.DateField(null=True, blank=True)
    partner_feedback = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-evaluation_date']
    
    def __str__(self):
        return f"Evaluation: {self.partner.name} - {self.evaluation_period_start} to {self.evaluation_period_end}"
    
    def average_rating(self):
        ratings = [
            self.rating_strategic_alignment,
            self.rating_communication,
            self.rating_reliability,
            self.rating_value_added,
            self.rating_innovation,
            self.rating_overall
        ]
        return sum(ratings) / len(ratings)


class PartnershipOpportunity(models.Model):
    """Potential partnership opportunities"""
    class OpportunityStatus(models.TextChoices):
        IDENTIFIED = 'identified', _('Identified')
        RESEARCHING = 'researching', _('Researching')
        CONTACTED = 'contacted', _('Contacted')
        DISCUSSING = 'discussing', _('In Discussion')
        PROPOSAL = 'proposal', _('Proposal Stage')
        NEGOTIATING = 'negotiating', _('Negotiating')
        WON = 'won', _('Won - Partnership Formed')
        LOST = 'lost', _('Lost'),
        ON_HOLD = 'on_hold', _('On Hold')
    
    # Opportunity Details
    name = models.CharField(max_length=255)
    description = models.TextField()
    organization_name = models.CharField(max_length=255, blank=True)
    organization_type = models.CharField(max_length=50, choices=PartnerOrganization.OrganizationType.choices, blank=True)
    
    # Potential Partnership
    potential_partnership_level = models.CharField(max_length=50, choices=PartnerOrganization.PartnershipLevel.choices)
    potential_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    potential_areas = models.JSONField(default=list, blank=True)
    
    # Source
    source = models.CharField(max_length=255, blank=True)
    source_type = models.CharField(max_length=50, choices=[
        ('referral', 'Referral'),
        ('research', 'Research'),
        ('event', 'Event/Conference'),
        ('outreach', 'Outreach'),
        ('inbound', 'Inbound Inquiry'),
        ('other', 'Other'),
    ], default='research')
    
    # Contact
    contact_name = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    
    # Status Tracking
    status = models.CharField(max_length=50, choices=OpportunityStatus.choices, default='identified')
    probability = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)], 
                                    help_text="Probability of success (%)")
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], default='medium')
    
    # Timeline
    identified_date = models.DateField()
    target_close_date = models.DateField(null=True, blank=True)
    actual_close_date = models.DateField(null=True, blank=True)
    
    # Team
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='partnership_opportunities')
    team_members = models.ManyToManyField(User, related_name='opportunity_teams', blank=True)
    
    # Notes & Strategy
    notes = models.TextField(blank=True)
    strategy = models.TextField(blank=True)
    challenges = models.TextField(blank=True)
    
    # Outcome
    outcome = models.TextField(blank=True)
    outcome_reason = models.TextField(blank=True)
    lessons_learned = models.TextField(blank=True)
    
    # If converted to actual partner
    converted_partner = models.ForeignKey(PartnerOrganization, on_delete=models.SET_NULL, null=True, blank=True, 
                                         related_name='converted_opportunities')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name_plural = 'Partnership opportunities'
        ordering = ['-identified_date', 'priority']
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"