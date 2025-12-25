from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.urls import path
from django.shortcuts import render, redirect
from django.db.models import Count, Avg, Q
from django.utils import timezone

from .models import (
    ProgramCategory, Program, ProgramApplication,
    ProgramUpdate, ProgramResource, ProgramParticipant, ProgramEvent
)


class ProgramResourceInline(admin.TabularInline):
    model = ProgramResource
    extra = 1
    fields = ('resource_type', 'title', 'file', 'url', 'is_public', 'access_level')
    readonly_fields = ('download_count', 'view_count')


class ProgramUpdateInline(admin.TabularInline):
    model = ProgramUpdate
    extra = 1
    fields = ('title', 'content', 'is_important', 'send_notification')
    readonly_fields = ('created_at', 'created_by')


class ProgramEventInline(admin.TabularInline):
    model = ProgramEvent
    extra = 1
    fields = ('title', 'start_datetime', 'end_datetime', 'location_type', 'is_published')


@admin.register(ProgramCategory)
class ProgramCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'display_order', 'is_active', 'program_count')
    list_editable = ('display_order', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    
    def program_count(self, obj):
        return obj.programs.count()
    program_count.short_description = 'Programs'


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'program_type', 'status', 'is_published', 
                   'is_featured', 'start_date', 'current_participants', 'views')
    list_filter = ('category', 'program_type', 'status', 'is_published', 
                  'is_featured', 'location_type', 'start_date')
    search_fields = ('title', 'short_description', 'full_description', 'slug')
    list_editable = ('is_featured', 'status', 'is_published')
    readonly_fields = ('uuid', 'views', 'applications_count', 'created_at', 
                      'updated_at', 'published_at', 'featured_image_preview')
    raw_id_fields = ('program_lead', 'created_by')
    filter_horizontal = ('coordinators', 'mentors', 'partners', 'funding_partners')
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'uuid', 'category', 'program_type', 'status')
        }),
        ('Description', {
            'fields': ('short_description', 'full_description', 'objectives', 'target_audience')
        }),
        ('Media', {
            'fields': ('featured_image_preview', 'featured_image', 'gallery', 'video_url')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date', 'application_deadline')
        }),
        ('Location & Capacity', {
            'fields': ('location_type', 'location', 'online_link', 'max_participants', 
                      'current_participants')
        }),
        ('Requirements', {
            'fields': ('eligibility_criteria', 'required_documents', 'skills_required'),
            'classes': ('collapse',)
        }),
        ('Financial', {
            'fields': ('is_free', 'fee_amount', 'fee_currency', 'scholarships_available', 
                      'funding_partners'),
            'classes': ('collapse',)
        }),
        ('Impact & Team', {
            'fields': ('impact_metrics', 'success_stories', 'program_lead', 'coordinators', 
                      'mentors', 'partners'),
            'classes': ('collapse',)
        }),
        ('SEO & Display', {
            'fields': ('meta_title', 'meta_description', 'is_featured', 'is_published')
        }),
        ('Statistics', {
            'fields': ('views', 'applications_count', 'completion_rate'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ProgramResourceInline, ProgramUpdateInline, ProgramEventInline]
    
    def featured_image_preview(self, obj):
        if obj.featured_image:
            return format_html('<img src="{}" style="max-height: 150px; max-width: 200px;" />', 
                             obj.featured_image.url)
        return "No image"
    featured_image_preview.short_description = "Featured Image Preview"
    
    actions = ['publish_selected', 'feature_selected', 'export_programs']
    
    def publish_selected(self, request, queryset):
        updated = queryset.update(is_published=True, published_at=timezone.now())
        self.message_user(request, f'{updated} programs published.')
    publish_selected.short_description = "Publish selected programs"
    
    def feature_selected(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} programs featured.')
    feature_selected.short_description = "Feature selected programs"


class ProgramApplicationInline(admin.TabularInline):
    model = ProgramApplication
    extra = 0
    fields = ('applicant', 'status', 'submitted_at', 'review_score')
    readonly_fields = ('submitted_at', 'review_score')
    can_delete = False
    max_num = 0  # Read-only inline


@admin.register(ProgramApplication)
class ProgramApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'program', 'applicant', 'status', 'submitted_at', 
                   'review_score', 'interview_scheduled')
    list_filter = ('status', 'program', 'submitted_at', 'reviewed_at')
    search_fields = ('applicant__username', 'applicant__email', 'program__title', 
                    'motivation_statement')
    list_editable = ('status',)
    readonly_fields = ('uuid', 'submitted_at', 'reviewed_at', 'created_at', 
                      'updated_at', 'resume_preview')
    raw_id_fields = ('program', 'applicant', 'reviewer')
    date_hierarchy = 'submitted_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('program', 'applicant', 'uuid', 'status')
        }),
        ('Application Content', {
            'fields': ('motivation_statement', 'relevant_experience', 'skills', 
                      'learning_objectives')
        }),
        ('Documents', {
            'fields': ('resume_preview', 'resume', 'portfolio', 'additional_docs')
        }),
        ('Review Process', {
            'fields': ('reviewer', 'review_notes', 'review_score', 'reviewed_at')
        }),
        ('Interview', {
            'fields': ('interview_scheduled', 'interview_notes', 'interview_score'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def resume_preview(self, obj):
        if obj.resume:
            return format_html('<a href="{}" target="_blank">View Resume</a>', 
                             obj.resume.url)
        return "No resume uploaded"
    resume_preview.short_description = "Resume"
    
    actions = ['shortlist_applications', 'accept_applications', 'reject_applications']
    
    def shortlist_applications(self, request, queryset):
        updated = queryset.update(status='shortlisted')
        self.message_user(request, f'{updated} applications shortlisted.')
    shortlist_applications.short_description = "Shortlist selected applications"
    
    def accept_applications(self, request, queryset):
        updated = queryset.update(status='accepted')
        # Create ProgramParticipant records for accepted applications
        for application in queryset.filter(status='accepted'):
            ProgramParticipant.objects.get_or_create(
                program=application.program,
                user=application.applicant,
                application=application,
                defaults={'status': 'active'}
            )
        self.message_user(request, f'{updated} applications accepted.')
    accept_applications.short_description = "Accept selected applications"


@admin.register(ProgramUpdate)
class ProgramUpdateAdmin(admin.ModelAdmin):
    list_display = ('title', 'program', 'is_important', 'send_notification', 'created_at')
    list_filter = ('is_important', 'send_notification', 'created_at')
    search_fields = ('title', 'content', 'program__title')
    raw_id_fields = ('program', 'created_by')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ProgramResource)
class ProgramResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'program', 'resource_type', 'is_public', 
                   'access_level', 'download_count', 'view_count')
    list_filter = ('resource_type', 'is_public', 'access_level')
    search_fields = ('title', 'description', 'program__title')
    raw_id_fields = ('program', 'uploaded_by')
    readonly_fields = ('download_count', 'view_count', 'created_at', 'updated_at')


@admin.register(ProgramParticipant)
class ProgramParticipantAdmin(admin.ModelAdmin):
    list_display = ('user', 'program', 'status', 'joined_at', 'attendance_rate', 
                   'certificate_issued')
    list_filter = ('status', 'program', 'certificate_issued', 'joined_at')
    search_fields = ('user__username', 'user__email', 'program__title', 
                    'certificate_serial')
    raw_id_fields = ('program', 'user', 'application')
    readonly_fields = ('joined_at', 'completed_at')  # REMOVED: 'created_at', 'updated_at'
    
    actions = ['issue_certificates', 'mark_as_completed']
    
    def issue_certificates(self, request, queryset):
        for participant in queryset.filter(status='completed', certificate_issued=False):
            participant.certificate_issued = True
            participant.certificate_serial = f"CERT-{participant.program.slug}-{participant.id}-{timezone.now().strftime('%Y%m%d')}"
            participant.save()
        self.message_user(request, f'Certificates issued for {queryset.count()} participants.')
    issue_certificates.short_description = "Issue certificates to selected participants"


@admin.register(ProgramEvent)
class ProgramEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'program', 'start_datetime', 'end_datetime', 
                   'location_type', 'is_published', 'current_attendees')
    list_filter = ('location_type', 'is_published', 'is_cancelled', 'start_datetime')
    search_fields = ('title', 'description', 'program__title')
    raw_id_fields = ('program',)
    filter_horizontal = ('presenters', 'resources')
    date_hierarchy = 'start_datetime'