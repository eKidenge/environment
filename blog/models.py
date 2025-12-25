from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

User = get_user_model()

class BlogCategory(models.Model):
    """Categories for blog posts"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#1a5fb4')
    icon = models.CharField(max_length=50, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    post_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _('Blog Category')
        verbose_name_plural = _('Blog Categories')
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name
    
    def update_post_count(self):
        self.post_count = self.posts.filter(is_published=True).count()
        self.save()


class BlogTag(models.Model):
    """Tags for blog posts"""
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    post_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def update_post_count(self):
        self.post_count = self.blogpost_set.filter(is_published=True).count()
        self.save()


class BlogPost(models.Model):
    class PostStatus(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        PUBLISHED = 'published', _('Published')
        SCHEDULED = 'scheduled', _('Scheduled')
        ARCHIVED = 'archived', _('Archived')
        TRASH = 'trash', _('Trash')
    
    class ContentType(models.TextChoices):
        ARTICLE = 'article', _('Article')
        NEWS = 'news', _('News')
        TUTORIAL = 'tutorial', _('Tutorial')
        CASE_STUDY = 'case_study', _('Case Study')
        INTERVIEW = 'interview', _('Interview')
        OPINION = 'opinion', _('Opinion')
        RESEARCH_SUMMARY = 'research_summary', _('Research Summary')
        EVENT_COVERAGE = 'event_coverage', _('Event Coverage')
    
    # Basic Information
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    excerpt = models.TextField(blank=True)
    content = models.TextField()
    content_type = models.CharField(max_length=50, choices=ContentType.choices, default='article')
    
    # Categorization
    category = models.ForeignKey(BlogCategory, on_delete=models.PROTECT, related_name='posts')
    tags = models.ManyToManyField(BlogTag, related_name='blog_posts', blank=True)
    related_posts = models.ManyToManyField('self', blank=True, symmetrical=True)
    
    # Authorship
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    co_authors = models.ManyToManyField(User, related_name='coauthored_posts', blank=True)
    editor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='edited_posts')
    
    # Media
    featured_image = models.ImageField(upload_to='blog/featured/%Y/%m/%d/')
    image_caption = models.CharField(max_length=255, blank=True)
    image_credit = models.CharField(max_length=255, blank=True)
    gallery = models.JSONField(default=list, blank=True)
    video_url = models.URLField(blank=True)
    
    # Publication Status
    status = models.CharField(max_length=20, choices=PostStatus.choices, default='draft')
    is_featured = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    allow_comments = models.BooleanField(default=True)
    
    # Scheduled Publishing
    published_at = models.DateTimeField(null=True, blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    meta_keywords = models.TextField(blank=True)
    canonical_url = models.URLField(blank=True)
    
    # Social Sharing
    social_image = models.ImageField(upload_to='blog/social/%Y/%m/%d/', null=True, blank=True)
    social_title = models.CharField(max_length=255, blank=True)
    social_description = models.TextField(blank=True)
    
    # Reading Experience
    read_time_minutes = models.PositiveIntegerField(default=5)
    word_count = models.PositiveIntegerField(default=0)
    
    # Engagement Metrics
    views = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    
    # Related Programs/Research
    related_programs = models.ManyToManyField('programs.Program', related_name='blog_posts', blank=True)
    related_publications = models.ManyToManyField('research.ResearchPublication', related_name='blog_posts', blank=True)
    related_projects = models.ManyToManyField('research.ResearchProject', related_name='blog_posts', blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                         related_name='last_modified_posts')
    
    class Meta:
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['slug', 'status']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['is_featured', 'status']),
            models.Index(fields=['published_at', 'status']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Calculate word count
        self.word_count = len(self.content.split())
        
        # Calculate read time (assuming 200 words per minute)
        self.read_time_minutes = max(1, self.word_count // 200)
        
        # Set published_at if publishing for first time
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        
        # If scheduled, set status to scheduled
        if self.scheduled_at and self.scheduled_at > timezone.now():
            self.status = 'scheduled'
        
        super().save(*args, **kwargs)
        
        # Update category post count
        if self.category:
            self.category.update_post_count()
        
        # Update tag post counts
        for tag in self.tags.all():
            tag.update_post_count()
    
    def is_published_now(self):
        """Check if post should be visible now"""
        if self.status != 'published':
            return False
        if self.scheduled_at and self.scheduled_at > timezone.now():
            return False
        return True
    
    def get_absolute_url(self):
        return f"/blog/{self.slug}/"


class BlogComment(models.Model):
    class CommentStatus(models.TextChoices):
        PENDING = 'pending', _('Pending Review')
        APPROVED = 'approved', _('Approved')
        SPAM = 'spam', _('Spam')
        TRASH = 'trash', _('Trash')
    
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    # Commenter Information
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='blog_comments')
    guest_name = models.CharField(max_length=100, blank=True)
    guest_email = models.EmailField(blank=True)
    guest_website = models.URLField(blank=True)
    
    # Content
    content = models.TextField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=CommentStatus.choices, default='pending')
    is_edited = models.BooleanField(default=False)
    edit_reason = models.TextField(blank=True)
    
    # Moderation
    moderated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                     related_name='moderated_comments')
    moderation_notes = models.TextField(blank=True)
    
    # Engagement
    likes = models.PositiveIntegerField(default=0)
    dislikes = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'status']),
            models.Index(fields=['author', 'status']),
        ]
    
    def __str__(self):
        return f"Comment by {self.get_author_name()} on {self.post.title}"
    
    def get_author_name(self):
        if self.author:
            return self.author.get_full_name() or self.author.username
        return self.guest_name or 'Anonymous'
    
    def save(self, *args, **kwargs):
        if self.status == 'approved' and not self.approved_at:
            self.approved_at = timezone.now()
        super().save(*args, **kwargs)
        
        # Update post comment count
        self.post.comment_count = self.post.comments.filter(status='approved').count()
        self.post.save(update_fields=['comment_count'])


class BlogLike(models.Model):
    """Track likes on blog posts"""
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='post_likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_likes')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['post', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} liked {self.post.title}"


class NewsletterPost(models.Model):
    """Blog posts sent as newsletters"""
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='newsletter_sends')
    newsletter_id = models.CharField(max_length=100, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    open_count = models.PositiveIntegerField(default=0)
    click_count = models.PositiveIntegerField(default=0)
    unsubscribe_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-sent_at']


class BlogView(models.Model):
    """Track detailed views for analytics"""
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='post_views')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    referrer = models.URLField(blank=True)
    session_id = models.CharField(max_length=100)
    time_on_page = models.PositiveIntegerField(default=0)  # in seconds
    scroll_depth = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]


class BlogSeries(models.Model):
    """Series of related blog posts"""
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField()
    posts = models.ManyToManyField(BlogPost, related_name='series', blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Blog series'
        ordering = ['display_order', '-created_at']
    
    def __str__(self):
        return self.title