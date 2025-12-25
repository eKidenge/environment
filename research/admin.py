from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.db.models import Count, Avg, Q
import json

from .models import (
    ResearchCategory, ResearchPublication, ResearchDataset,
    ResearchProject, ResearchTool, LiteratureReview
)


@admin.register(ResearchCategory)
class ResearchCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'display_order', 'is_active', 'publication_count')
    list_editable = ('display_order', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    
    def publication_count(self, obj):
        return obj.publications.count()
    publication_count.short_description = 'Publications'


class ResearchPublicationInline(admin.TabularInline):
    model = ResearchPublication.contributors.through
    extra = 1
    verbose_name = "Contributor"
    verbose_name_plural = "Contributors"


@admin.register(ResearchPublication)
class ResearchPublicationAdmin(admin.ModelAdmin):
    list_display = ('title', 'publication_type', 'category', 'publication_date', 
                   'peer_review_status', 'is_featured', 'views', 'downloads', 'citation_count')
    list_filter = ('publication_type', 'category', 'peer_review_status', 'is_featured', 
                  'is_published', 'publication_date')
    search_fields = ('title', 'abstract', 'authors', 'doi', 'keywords')
    list_editable = ('is_featured', 'peer_review_status')
    readonly_fields = ('uuid', 'views', 'downloads', 'citation_count', 'created_at', 
                      'updated_at', 'pdf_preview', 'citation_formatted')
    raw_id_fields = ('corresponding_author',)
    filter_horizontal = ('contributors', 'related_programs')
    date_hierarchy = 'publication_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'uuid', 'publication_type', 'category')
        }),
        ('Authors and Abstract', {
            'fields': ('authors', 'corresponding_author', 'contributors', 'abstract', 'keywords')
        }),
        ('Publication Details', {
            'fields': ('journal_name', 'conference_name', 'publisher', 'publication_date',
                      'volume', 'issue', 'pages', 'full_text', 'highlights')
        }),
        ('Identifiers', {
            'fields': ('doi', 'issn', 'isbn', 'arxiv_id', 'pmid'),
            'classes': ('collapse',)
        }),
        ('Files and Links', {
            'fields': ('pdf_preview', 'pdf_file', 'supplementary_files', 
                      'data_repository_url', 'code_repository_url')
        }),
        ('Licensing and Access', {
            'fields': ('license', 'copyright_holder', 'access_rights'),
            'classes': ('collapse',)
        }),
        ('Peer Review', {
            'fields': ('peer_review_status', 'review_comments', 'reviewers'),
            'classes': ('collapse',)
        }),
        ('Citations and Impact', {
            'fields': ('citation_formatted', 'citation_count', 'references', 'citations',
                      'altmetric_score', 'impact_factor', 'field_citation_ratio'),
            'classes': ('collapse',)
        }),
        ('Funding', {
            'fields': ('funding_agencies', 'grant_numbers', 'acknowledgements'),
            'classes': ('collapse',)
        }),
        ('Display and SEO', {
            'fields': ('is_featured', 'is_published', 'featured_image', 
                      'meta_title', 'meta_description')
        }),
        ('Statistics', {
            'fields': ('views', 'downloads', 'shares'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'submitted_at', 'accepted_at'),
            'classes': ('collapse',)
        }),
    )
    
    def pdf_preview(self, obj):
        if obj.pdf_file:
            return format_html('<a href="{}" target="_blank">View PDF</a>', obj.pdf_file.url)
        return "No PDF"
    pdf_preview.short_description = "PDF"
    
    def citation_formatted(self, obj):
        return obj.generate_citation('apa')
    citation_formatted.short_description = "APA Citation"
    
    actions = ['mark_as_peer_reviewed', 'export_publications', 'update_altmetrics']
    
    def mark_as_peer_reviewed(self, request, queryset):
        updated = queryset.update(peer_review_status='peer_reviewed')
        self.message_user(request, f'{updated} publications marked as peer reviewed.')
    mark_as_peer_reviewed.short_description = "Mark as peer reviewed"


@admin.register(ResearchDataset)
class ResearchDatasetAdmin(admin.ModelAdmin):
    list_display = ('title', 'dataset_type', 'version', 'access_type', 'is_verified', 
                   'views', 'downloads', 'created_at')
    list_filter = ('dataset_type', 'access_type', 'license_type', 'is_verified', 'created_at')
    search_fields = ('title', 'description', 'doi', 'keywords')
    readonly_fields = ('uuid', 'views', 'downloads', 'citations', 'created_at', 'updated_at')
    filter_horizontal = ('related_publications',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'uuid', 'dataset_type', 'description')
        }),
        ('Creators and Contact', {
            'fields': ('creators', 'contact_email')
        }),
        ('Content and Coverage', {
            'fields': ('keywords', 'variables', 'methodology', 
                      'temporal_coverage_start', 'temporal_coverage_end', 'spatial_coverage')
        }),
        ('Files and Storage', {
            'fields': ('file_formats', 'total_size_gb', 'file_count', 
                      'storage_location', 'download_url', 'api_endpoint')
        }),
        ('Metadata and Identifiers', {
            'fields': ('version', 'doi', 'metadata_standard')
        }),
        ('Licensing and Access', {
            'fields': ('license_type', 'access_type', 'embargo_date')
        }),
        ('Quality and Validation', {
            'fields': ('quality_metrics', 'validation_report', 'is_verified', 'verified_by')
        }),
        ('Statistics', {
            'fields': ('views', 'downloads', 'citations'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ResearchProject)
class ResearchProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'principal_investigator', 'start_date', 
                   'end_date', 'progress_percentage', 'is_featured', 'budget_amount')
    list_filter = ('status', 'is_featured', 'is_public', 'start_date')
    search_fields = ('title', 'abstract', 'objectives', 'research_questions')
    list_editable = ('status', 'is_featured')
    readonly_fields = ('uuid', 'created_at', 'updated_at', 'featured_image_preview')
    raw_id_fields = ('principal_investigator',)
    filter_horizontal = ('co_investigators', 'research_assistants', 'publications', 
                        'datasets', 'partners')
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'uuid', 'status')
        }),
        ('Description', {
            'fields': ('abstract', 'objectives', 'research_questions', 'methodology')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date')
        }),
        ('Team', {
            'fields': ('principal_investigator', 'co_investigators', 'research_assistants')
        }),
        ('Funding', {
            'fields': ('funding_agency', 'grant_number', 'budget_amount', 'budget_currency'),
            'classes': ('collapse',)
        }),
        ('Outputs', {
            'fields': ('publications', 'datasets', 'deliverables'),
            'classes': ('collapse',)
        }),
        ('Collaboration', {
            'fields': ('collaborating_institutions', 'partners'),
            'classes': ('collapse',)
        }),
        ('Progress Tracking', {
            'fields': ('milestones', 'progress_percentage', 'progress_notes')
        }),
        ('Impact', {
            'fields': ('impact_statement', 'policy_implications', 'sustainability_plan'),
            'classes': ('collapse',)
        }),
        ('Media', {
            'fields': ('featured_image_preview', 'featured_image', 'gallery')
        }),
        ('Display', {
            'fields': ('is_featured', 'is_public')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def featured_image_preview(self, obj):
        if obj.featured_image:
            return format_html('<img src="{}" style="max-height: 150px; max-width: 200px;" />', 
                             obj.featured_image.url)
        return "No image"
    featured_image_preview.short_description = "Featured Image Preview"


@admin.register(ResearchTool)
class ResearchToolAdmin(admin.ModelAdmin):
    list_display = ('name', 'tool_type', 'version', 'license', 'download_count', 
                   'citation_count', 'released_at')
    list_filter = ('tool_type', 'license', 'created_at')
    search_fields = ('name', 'description', 'programming_language')
    readonly_fields = ('uuid', 'download_count', 'citation_count', 'created_at', 'updated_at')
    filter_horizontal = ('developers', 'maintainers', 'related_publications', 'related_projects')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'uuid', 'tool_type', 'description')
        }),
        ('Technical Details', {
            'fields': ('version', 'programming_language', 'dependencies', 'system_requirements')
        }),
        ('Access', {
            'fields': ('repository_url', 'documentation_url', 'demo_url', 'license')
        }),
        ('Team', {
            'fields': ('developers', 'maintainers'),
            'classes': ('collapse',)
        }),
        ('Related Work', {
            'fields': ('related_publications', 'related_projects'),
            'classes': ('collapse',)
        }),
        ('Usage Statistics', {
            'fields': ('download_count', 'citation_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'released_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LiteratureReview)
class LiteratureReviewAdmin(admin.ModelAdmin):
    list_display = ('title', 'studies_included', 'studies_excluded', 'completed_at', 'created_at')
    search_fields = ('title', 'research_question', 'key_findings', 'recommendations')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    filter_horizontal = ('related_publications',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'uuid')
        }),
        ('Review Details', {
            'fields': ('research_question', 'inclusion_criteria', 'exclusion_criteria', 
                      'search_strategy')
        }),
        ('Analysis', {
            'fields': ('studies_included', 'studies_excluded', 'synthesis_method')
        }),
        ('Results', {
            'fields': ('key_findings', 'research_gaps', 'recommendations')
        }),
        ('Metadata', {
            'fields': ('related_publications', 'conducted_by', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )