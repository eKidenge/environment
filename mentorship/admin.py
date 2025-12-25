from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.utils import timezone

from .models import (
    MentorshipProgram, MentorshipApplication, MentorshipMatch,
    MentorshipSession, MentorshipResource, MentorshipFeedback,
    MentorshipGoal
)


class MentorshipApplicationInline(admin.TabularInline):
    model = MentorshipApplication
    extra = 0
    fields = ('applicant', 'applying_as', 'status', 'submitted_at', 'review_score')
    readonly_fields = ('submitted_at', 'review_score')
    can_delete = False
    max_num = 5


class MentorshipMatchInline(admin.TabularInline):
    model = MentorshipMatch
    extra = 0
    fields = ('mentor', 'mentee', 'status', 'match_score', 'started_at')
    readonly_fields = ('match_score', 'started_at')
    can_delete = False
    max_num = 5


@admin.register(MentorshipProgram)
class MentorshipProgramAdmin(admin.ModelAdmin):
    list_display = ('title', 'program_type', 'status', 'application_deadline', 
                   'program_start', 'current_mentors', 'current_mentees', 
                   'is_featured', 'is_published')
    list_filter = ('program_type', 'status', 'format', 'is_featured', 'is_published', 
                  'application_start', 'application_deadline')
    search_fields = ('title', 'description', 'objectives', 'slug')
    list_editable = ('is_featured', 'status', 'is_published')
    readonly_fields = ('uuid', 'applications_count', 'matches_count', 'success_rate',
                      'created_at', 'updated_at', 'featured_image_preview')
    raw_id_fields = ('program_coordinator', 'created_by')
    filter_horizontal = ('mentors',)
    date_hierarchy = 'program_start'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'uuid', 'program_type', 'status')
        }),
        ('Description', {
            'fields': ('description', 'objectives', 'benefits', 'curriculum')
        }),
        ('Target Audience', {
            'fields': ('target_audience', 'prerequisites', 'skills_focus'),
            'classes': ('collapse',)
        }),
        ('Structure', {
            'fields': ('duration_weeks', 'time_commitment', 'format')
        }),
        ('Capacity', {
            'fields': ('max_mentors', 'max_mentees', 'current_mentors', 'current_mentees')
        }),
        ('Timeline', {
            'fields': ('application_start', 'application_deadline', 'program_start', 'program_end')
        }),
        ('Matching', {
            'fields': ('matching_criteria', 'matching_algorithm', 'allow_self_matching'),
            'classes': ('collapse',)
        }),
        ('Team', {
            'fields': ('program_coordinator', 'mentors'),
            'classes': ('collapse',)
        }),
        ('Resources & Evaluation', {
            'fields': ('resources', 'toolkit', 'success_metrics', 'evaluation_method'),
            'classes': ('collapse',)
        }),
        ('Media', {
            'fields': ('featured_image_preview', 'featured_image')
        }),
        ('SEO & Display', {
            'fields': ('is_featured', 'is_published', 'meta_title', 'meta_description')
        }),
        ('Statistics', {
            'fields': ('applications_count', 'matches_count', 'success_rate'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [MentorshipApplicationInline, MentorshipMatchInline]
    
    def featured_image_preview(self, obj):
        if obj.featured_image:
            return format_html('<img src="{}" style="max-height: 150px; max-width: 200px;" />', 
                             obj.featured_image.url)
        return "No image"
    featured_image_preview.short_description = "Featured Image Preview"
    
    actions = ['publish_programs', 'feature_programs', 'calculate_stats']
    
    def publish_programs(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, f'{updated} programs published.')
    publish_programs.short_description = "Publish selected programs"
    
    def feature_programs(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} programs featured.')
    feature_programs.short_description = "Feature selected programs"


@admin.register(MentorshipApplication)
class MentorshipApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'program', 'applicant', 'applying_as', 'status', 
                   'submitted_at', 'review_score', 'interview_scheduled')
    list_filter = ('status', 'applying_as', 'program', 'submitted_at', 'reviewed_at')
    search_fields = ('applicant__username', 'applicant__email', 'program__title', 
                    'motivation_statement', 'experience_summary')
    list_editable = ('status',)
    readonly_fields = ('uuid', 'submitted_at', 'reviewed_at', 'created_at', 
                      'updated_at', 'resume_preview')
    raw_id_fields = ('program', 'applicant', 'reviewer')
    date_hierarchy = 'submitted_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('program', 'applicant', 'uuid', 'applying_as', 'status')
        }),
        ('Application Content', {
            'fields': ('motivation_statement', 'experience_summary', 'learning_goals',
                      'expertise_areas', 'availability', 'preferences')
        }),
        ('Documents', {
            'fields': ('resume_preview', 'resume', 'portfolio', 'reference_letters')
        }),
        ('Review Process', {
            'fields': ('reviewer', 'review_notes', 'review_score', 'reviewed_at')
        }),
        ('Interview', {
            'fields': ('interview_scheduled', 'interview_notes'),
            'classes': ('collapse',)
        }),
        ('Matching', {
            'fields': ('match_preferences', 'match_score'),
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
        return "No resume"
    resume_preview.short_description = "Resume"
    
    actions = ['shortlist_applications', 'accept_applications', 'reject_applications']
    
    def shortlist_applications(self, request, queryset):
        updated = queryset.update(status='shortlisted')
        self.message_user(request, f'{updated} applications shortlisted.')
    shortlist_applications.short_description = "Shortlist selected applications"


class MentorshipSessionInline(admin.TabularInline):
    model = MentorshipSession
    extra = 0
    fields = ('title', 'scheduled_start', 'status', 'location_type')
    readonly_fields = ('scheduled_start',)
    can_delete = False
    max_num = 5


class MentorshipGoalInline(admin.TabularInline):
    model = MentorshipGoal
    extra = 0
    fields = ('title', 'status', 'priority', 'progress_percentage', 'target_date')
    readonly_fields = ('progress_percentage', 'target_date')
    can_delete = False
    max_num = 5


@admin.register(MentorshipMatch)
class MentorshipMatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'program', 'mentor', 'mentee', 'status', 'match_score', 
                   'started_at', 'meetings_held', 'milestones_completed')
    list_filter = ('status', 'program', 'created_at', 'started_at')
    search_fields = ('mentor__username', 'mentor__email', 'mentee__username', 
                    'mentee__email', 'program__title')
    list_editable = ('status',)
    readonly_fields = ('uuid', 'proposed_at', 'accepted_at', 'started_at', 
                      'completed_at', 'created_at', 'updated_at')
    raw_id_fields = ('program', 'mentor', 'mentee', 'matched_by')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Match Information', {
            'fields': ('program', 'mentor', 'mentee', 'uuid', 'status')
        }),
        ('Match Details', {
            'fields': ('match_score', 'match_reason', 'compatibility_factors')
        }),
        ('Agreement', {
            'fields': ('goals', 'meeting_frequency', 'communication_channels', 
                      'agreement_document'),
            'classes': ('collapse',)
        }),
        ('Progress Tracking', {
            'fields': ('meetings_held', 'milestones_completed', 'progress_notes')
        }),
        ('Feedback', {
            'fields': ('mentor_feedback', 'mentee_feedback', 'overall_rating'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('proposed_at', 'accepted_at', 'started_at', 'completed_at',
                      'created_at', 'updated_at', 'matched_by'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [MentorshipSessionInline, MentorshipGoalInline]
    
    actions = ['propose_matches', 'activate_matches', 'complete_matches']
    
    def propose_matches(self, request, queryset):
        updated = queryset.update(status='proposed', proposed_at=timezone.now())
        self.message_user(request, f'{updated} matches proposed.')
    propose_matches.short_description = "Propose selected matches"
    
    def activate_matches(self, request, queryset):
        updated = queryset.update(status='active', started_at=timezone.now())
        self.message_user(request, f'{updated} matches activated.')
    activate_matches.short_description = "Activate selected matches"


@admin.register(MentorshipSession)
class MentorshipSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'match', 'scheduled_start', 'status', 'location_type', 
                   'session_rating', 'created_at')
    list_filter = ('status', 'location_type', 'scheduled_start')
    search_fields = ('title', 'description', 'match__mentor__username', 
                    'match__mentee__username', 'agenda')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('match', 'created_by')
    date_hierarchy = 'scheduled_start'
    
    fieldsets = (
        ('Session Information', {
            'fields': ('match', 'title', 'description', 'agenda')
        }),
        ('Timing', {
            'fields': ('scheduled_start', 'scheduled_end', 'actual_start', 'actual_end', 'timezone')
        }),
        ('Location/Platform', {
            'fields': ('location_type', 'meeting_link', 'location')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Resources', {
            'fields': ('resources',),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('preparation_notes', 'session_notes', 'action_items'),
            'classes': ('collapse',)
        }),
        ('Feedback', {
            'fields': ('mentor_feedback', 'mentee_feedback', 'session_rating'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MentorshipResource)
class MentorshipResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'resource_type', 'program', 'match', 'access_level', 
                   'download_count', 'created_at')
    list_filter = ('resource_type', 'access_level', 'created_at')
    search_fields = ('title', 'description', 'content', 'tags')
    readonly_fields = ('download_count', 'created_at', 'updated_at')
    raw_id_fields = ('program', 'match', 'uploaded_by')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('resource_type', 'title', 'description')
        }),
        ('Reference', {
            'fields': ('program', 'match')
        }),
        ('Content', {
            'fields': ('file', 'url', 'content')
        }),
        ('Access', {
            'fields': ('access_level', 'tags')
        }),
        ('Statistics', {
            'fields': ('download_count',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'uploaded_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MentorshipFeedback)
class MentorshipFeedbackAdmin(admin.ModelAdmin):
    list_display = ('feedback_type', 'provided_by', 'provided_for', 'rating_overall', 
                   'would_recommend', 'is_anonymous', 'created_at')
    list_filter = ('feedback_type', 'is_anonymous', 'is_approved', 'created_at')
    search_fields = ('strengths', 'areas_for_improvement', 'suggestions', 
                    'provided_by__username', 'provided_for__username')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('program', 'match', 'session', 'provided_by', 'provided_for')
    
    fieldsets = (
        ('Feedback Type & Reference', {
            'fields': ('feedback_type', 'program', 'match', 'session')
        }),
        ('Participants', {
            'fields': ('provided_by', 'provided_for', 'is_anonymous')
        }),
        ('Ratings (1-5)', {
            'fields': ('rating_knowledge', 'rating_communication', 'rating_support', 'rating_overall')
        }),
        ('Qualitative Feedback', {
            'fields': ('strengths', 'areas_for_improvement', 'suggestions')
        }),
        ('Impact', {
            'fields': ('key_learnings', 'application_plans', 'would_recommend'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_approved',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MentorshipGoal)
class MentorshipGoalAdmin(admin.ModelAdmin):
    list_display = ('title', 'match', 'status', 'priority', 'progress_percentage', 
                   'target_date', 'completion_date')
    list_filter = ('status', 'priority', 'category', 'target_date')
    search_fields = ('title', 'description', 'success_criteria', 'match__mentor__username')
    list_editable = ('status', 'priority', 'progress_percentage')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('match', 'created_by')
    date_hierarchy = 'target_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('match', 'title', 'description', 'category', 'priority')
        }),
        ('Timeline', {
            'fields': ('target_date', 'start_date', 'completion_date')
        }),
        ('Progress', {
            'fields': ('status', 'progress_percentage')
        }),
        ('Metrics & Evidence', {
            'fields': ('success_criteria', 'evidence'),
            'classes': ('collapse',)
        }),
        ('Review Notes', {
            'fields': ('mentor_notes', 'mentee_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )