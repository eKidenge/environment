from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()

class ResearchCategory(models.Model):
    """Research categories (Climate Change, Biodiversity, etc.)"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _('Research Category')
        verbose_name_plural = _('Research Categories')
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name


class ResearchPublication(models.Model):
    class PublicationType(models.TextChoices):
        JOURNAL_ARTICLE = 'journal_article', _('Journal Article')
        CONFERENCE_PAPER = 'conference_paper', _('Conference Paper')
        BOOK = 'book', _('Book')
        BOOK_CHAPTER = 'book_chapter', _('Book Chapter')
        THESIS = 'thesis', _('Thesis/Dissertation')
        REPORT = 'report', _('Report')
        POLICY_BRIEF = 'policy_brief', _('Policy Brief')
        WORKING_PAPER = 'working_paper', _('Working Paper')
        DATA_PAPER = 'data_paper', _('Data Paper')
        PREPRINT = 'preprint', _('Preprint')
    
    class PeerReviewStatus(models.TextChoices):
        NOT_REVIEWED = 'not_reviewed', _('Not Reviewed')
        UNDER_REVIEW = 'under_review', _('Under Review')
        PEER_REVIEWED = 'peer_reviewed', _('Peer Reviewed')
        REJECTED = 'rejected', _('Rejected')
    
    # Basic Information
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=500)
    slug = models.SlugField(max_length=500, unique=True)
    publication_type = models.CharField(max_length=50, choices=PublicationType.choices)
    category = models.ForeignKey(ResearchCategory, on_delete=models.PROTECT, related_name='publications')
    
    # Authors and Contributors
    authors = models.JSONField(default=list)  # List of author objects
    corresponding_author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='corresponding_publications')
    contributors = models.ManyToManyField(User, related_name='contributed_publications', blank=True)
    
    # Abstract and Content
    abstract = models.TextField()
    keywords = models.JSONField(default=list, blank=True)
    full_text = models.TextField(blank=True)
    highlights = models.JSONField(default=list, blank=True)
    
    # Publication Details
    journal_name = models.CharField(max_length=255, blank=True)
    conference_name = models.CharField(max_length=255, blank=True)
    publisher = models.CharField(max_length=255, blank=True)
    publication_date = models.DateField()
    volume = models.CharField(max_length=50, blank=True)
    issue = models.CharField(max_length=50, blank=True)
    pages = models.CharField(max_length=50, blank=True)
    
    # Identifiers
    doi = models.CharField(max_length=100, blank=True)
    issn = models.CharField(max_length=50, blank=True)
    isbn = models.CharField(max_length=50, blank=True)
    arxiv_id = models.CharField(max_length=50, blank=True)
    pmid = models.CharField(max_length=50, blank=True)
    
    # Files
    pdf_file = models.FileField(upload_to='research/pdfs/%Y/%m/%d/', null=True, blank=True)
    supplementary_files = models.JSONField(default=list, blank=True)
    data_repository_url = models.URLField(blank=True)
    code_repository_url = models.URLField(blank=True)
    
    # Licensing
    license = models.CharField(max_length=100, blank=True)
    copyright_holder = models.CharField(max_length=255, blank=True)
    access_rights = models.CharField(max_length=50, choices=[
        ('open_access', 'Open Access'),
        ('subscription', 'Subscription'),
        ('embargoed', 'Embargoed'),
        ('restricted', 'Restricted'),
    ], default='open_access')
    
    # Peer Review
    peer_review_status = models.CharField(max_length=50, choices=PeerReviewStatus.choices, default='not_reviewed')
    review_comments = models.TextField(blank=True)
    reviewers = models.JSONField(default=list, blank=True)
    
    # Citations
    citation_count = models.PositiveIntegerField(default=0)
    reference_count = models.PositiveIntegerField(default=0)
    citations = models.JSONField(default=list, blank=True)
    references = models.JSONField(default=list, blank=True)
    
    # Impact Metrics
    altmetric_score = models.FloatField(null=True, blank=True)
    altmetric_details = models.JSONField(default=dict, blank=True)
    impact_factor = models.FloatField(null=True, blank=True)
    field_citation_ratio = models.FloatField(null=True, blank=True)
    
    # Funding
    funding_agencies = models.JSONField(default=list, blank=True)
    grant_numbers = models.JSONField(default=list, blank=True)
    acknowledgements = models.TextField(blank=True)
    
    # Related Projects
    related_programs = models.ManyToManyField('programs.Program', related_name='research_publications', blank=True)
    related_projects = models.JSONField(default=list, blank=True)
    
    # SEO & Display
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    featured_image = models.ImageField(upload_to='research/featured/%Y/%m/%d/', null=True, blank=True)
    
    # Statistics
    views = models.PositiveIntegerField(default=0)
    downloads = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-publication_date', '-created_at']
        indexes = [
            models.Index(fields=['slug', 'publication_type']),
            models.Index(fields=['publication_date', 'is_published']),
            models.Index(fields=['doi', 'is_published']),
        ]
    
    def __str__(self):
        return self.title
    
    def generate_citation(self, style='apa'):
        """Generate citation in different styles"""
        authors_text = ', '.join([author.get('name', '') for author in self.authors[:3]])
        if len(self.authors) > 3:
            authors_text += ' et al.'
        
        if style == 'apa':
            return f"{authors_text} ({self.publication_date.year}). {self.title}. {self.journal_name}, {self.volume}({self.issue}), {self.pages}. https://doi.org/{self.doi}"
        elif style == 'mla':
            return f"{authors_text}. \"{self.title}.\" {self.journal_name}, vol. {self.volume}, no. {self.issue}, {self.publication_date.year}, pp. {self.pages}."
        else:
            return f"{authors_text} ({self.publication_date}). {self.title}. {self.journal_name}"


class ResearchDataset(models.Model):
    class DatasetType(models.TextChoices):
        OBSERVATIONAL = 'observational', _('Observational')
        EXPERIMENTAL = 'experimental', _('Experimental')
        SIMULATION = 'simulation', _('Simulation')
        SURVEY = 'survey', _('Survey')
        GEOSPATIAL = 'geospatial', _('Geospatial')
        TIME_SERIES = 'time_series', _('Time Series')
        IMAGE = 'image', _('Image Data')
        GENOMIC = 'genomic', _('Genomic')
    
    class LicenseType(models.TextChoices):
        CC_BY = 'cc_by', _('CC BY')
        CC_BY_SA = 'cc_by_sa', _('CC BY-SA')
        CC_BY_NC = 'cc_by_nc', _('CC BY-NC')
        CC0 = 'cc0', _('CC0 Public Domain')
        MIT = 'mit', _('MIT License')
        APACHE = 'apache', _('Apache License 2.0')
        PROPRIETARY = 'proprietary', _('Proprietary')
        OTHER = 'other', _('Other')
    
    # Basic Information
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=500)
    slug = models.SlugField(max_length=500, unique=True)
    dataset_type = models.CharField(max_length=50, choices=DatasetType.choices)
    description = models.TextField()
    
    # Authors and Contributors
    creators = models.JSONField(default=list)
    contact_email = models.EmailField()
    
    # Content
    keywords = models.JSONField(default=list, blank=True)
    variables = models.JSONField(default=list, blank=True)
    methodology = models.TextField(blank=True)
    
    # Temporal and Spatial Coverage
    temporal_coverage_start = models.DateField(null=True, blank=True)
    temporal_coverage_end = models.DateField(null=True, blank=True)
    spatial_coverage = models.JSONField(default=dict, blank=True)
    
    # Files and Storage
    file_formats = models.JSONField(default=list, blank=True)
    total_size_gb = models.FloatField(default=0)
    file_count = models.PositiveIntegerField(default=0)
    storage_location = models.CharField(max_length=255, blank=True)
    download_url = models.URLField(blank=True)
    api_endpoint = models.URLField(blank=True)
    
    # Metadata
    version = models.CharField(max_length=50, default='1.0')
    doi = models.CharField(max_length=100, blank=True)
    metadata_standard = models.CharField(max_length=100, blank=True)
    
    # Licensing and Access
    license_type = models.CharField(max_length=50, choices=LicenseType.choices, default='cc_by')
    access_type = models.CharField(max_length=50, choices=[
        ('open', 'Open Access'),
        ('embargoed', 'Embargoed'),
        ('restricted', 'Restricted'),
        ('controlled', 'Controlled Access'),
    ], default='open')
    embargo_date = models.DateField(null=True, blank=True)
    
    # Quality and Validation
    quality_metrics = models.JSONField(default=dict, blank=True)
    validation_report = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Related Publications
    related_publications = models.ManyToManyField(ResearchPublication, related_name='datasets', blank=True)
    
    # Usage Statistics
    views = models.PositiveIntegerField(default=0)
    downloads = models.PositiveIntegerField(default=0)
    citations = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug', 'dataset_type']),
            models.Index(fields=['doi', 'is_verified']),
        ]
    
    def __str__(self):
        return self.title


class ResearchProject(models.Model):
    class ProjectStatus(models.TextChoices):
        PLANNING = 'planning', _('Planning')
        ONGOING = 'ongoing', _('Ongoing')
        COMPLETED = 'completed', _('Completed')
        ON_HOLD = 'on_hold', _('On Hold')
        CANCELLED = 'cancelled', _('Cancelled')
    
    # Basic Information
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    status = models.CharField(max_length=20, choices=ProjectStatus.choices, default='planning')
    
    # Description
    abstract = models.TextField()
    objectives = models.JSONField(default=list, blank=True)
    research_questions = models.JSONField(default=list, blank=True)
    methodology = models.TextField(blank=True)
    
    # Timeline
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    # Team
    principal_investigator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='led_projects')
    co_investigators = models.ManyToManyField(User, related_name='co_investigated_projects', blank=True)
    research_assistants = models.ManyToManyField(User, related_name='assisted_projects', blank=True)
    
    # Funding
    funding_agency = models.CharField(max_length=255, blank=True)
    grant_number = models.CharField(max_length=100, blank=True)
    budget_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    budget_currency = models.CharField(max_length=3, default='USD')
    
    # Outputs
    publications = models.ManyToManyField(ResearchPublication, related_name='projects', blank=True)
    datasets = models.ManyToManyField(ResearchDataset, related_name='projects', blank=True)
    deliverables = models.JSONField(default=list, blank=True)
    
    # Collaboration
    collaborating_institutions = models.JSONField(default=list, blank=True)
    partners = models.ManyToManyField('partners.PartnerOrganization', related_name='research_projects', blank=True)
    
    # Progress Tracking
    milestones = models.JSONField(default=list, blank=True)
    progress_percentage = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    progress_notes = models.TextField(blank=True)
    
    # Impact
    impact_statement = models.TextField(blank=True)
    policy_implications = models.TextField(blank=True)
    sustainability_plan = models.TextField(blank=True)
    
    # Media
    featured_image = models.ImageField(upload_to='research/projects/%Y/%m/%d/', null=True, blank=True)
    gallery = models.JSONField(default=list, blank=True)
    
    # SEO & Display
    is_featured = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug', 'status']),
            models.Index(fields=['principal_investigator', 'status']),
        ]
    
    def __str__(self):
        return self.title


class ResearchTool(models.Model):
    class ToolType(models.TextChoices):
        SOFTWARE = 'software', _('Software')
        MODEL = 'model', _('Model')
        FRAMEWORK = 'framework', _('Framework')
        PROTOCOL = 'protocol', _('Protocol')
        INSTRUMENT = 'instrument', _('Instrument')
        METHODOLOGY = 'methodology', _('Methodology')
    
    # Basic Information
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    tool_type = models.CharField(max_length=50, choices=ToolType.choices)
    description = models.TextField()
    
    # Technical Details
    version = models.CharField(max_length=50, default='1.0')
    programming_language = models.CharField(max_length=100, blank=True)
    dependencies = models.JSONField(default=list, blank=True)
    system_requirements = models.TextField(blank=True)
    
    # Access
    repository_url = models.URLField(blank=True)
    documentation_url = models.URLField(blank=True)
    demo_url = models.URLField(blank=True)
    license = models.CharField(max_length=100, blank=True)
    
    # Authors
    developers = models.ManyToManyField(User, related_name='developed_tools', blank=True)
    maintainers = models.ManyToManyField(User, related_name='maintained_tools', blank=True)
    
    # Related Work
    related_publications = models.ManyToManyField(ResearchPublication, related_name='tools', blank=True)
    related_projects = models.ManyToManyField(ResearchProject, related_name='tools', blank=True)
    
    # Usage
    download_count = models.PositiveIntegerField(default=0)
    citation_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    released_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class LiteratureReview(models.Model):
    """Systematic literature reviews"""
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=500)
    slug = models.SlugField(max_length=500, unique=True)
    
    # Review Details
    research_question = models.TextField()
    inclusion_criteria = models.JSONField(default=list, blank=True)
    exclusion_criteria = models.JSONField(default=list, blank=True)
    search_strategy = models.TextField(blank=True)
    
    # Analysis
    studies_included = models.PositiveIntegerField(default=0)
    studies_excluded = models.PositiveIntegerField(default=0)
    synthesis_method = models.CharField(max_length=100, blank=True)
    
    # Results
    key_findings = models.JSONField(default=list, blank=True)
    research_gaps = models.JSONField(default=list, blank=True)
    recommendations = models.TextField(blank=True)
    
    # Related
    related_publications = models.ManyToManyField(ResearchPublication, related_name='literature_reviews', blank=True)
    conducted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title