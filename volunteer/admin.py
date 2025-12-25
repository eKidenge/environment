from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.utils import timezone

from .models import (
    VolunteerOpportunity, VolunteerApplication, VolunteerAssignment,
    VolunteerTimeLog, VolunteerSkill, VolunteerAward, VolunteerEvent
)


class VolunteerApplicationInline(admin.TabularInline):
    model = VolunteerApplication
    extra = 0
    fields = ('applicant', 'status', 'submitted_at', 'review_score')
    readonly_fields = ('submitted_at', 'review_score')
    can_delete = False
    max_num = 5


@admin.register(VolunteerOpportunity)
class VolunteerOpportunityAdmin(admin.ModelAdmin):
    list_display = ('title', 'opportunity_type', 'status', 'city', 'country', 
                   'positions_filled', 'positions_available', 'fill_percentage', 
                   'is_featured', 'is_published', 'start_date')
    list_filter = ('opportunity_type', 'status', 'skill_level', 'country', 
                  'city', 'is_featured', 'is_published', 'start_date')
    search_fields = ('title', 'description', 'responsibilities', 'city', 'country', 'slug')
    list_editable = ('is_featured', 'status', 'is_published')
    readonly_fields = ('uuid', 'views', 'applications_count', 'completion_rate', 
                      'volunteer_satisfaction', 'created_at', 'updated_at', 
                      'published_at', 'fill_percentage_display', 'featured_image_preview')
    raw_id_fields = ('supervisor', 'team_lead', 'created_by')
    filter_horizontal = ('related_programs', 'related_projects')
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'uuid', 'opportunity_type', 'status')
        }),
        ('Description', {
            'fields': ('description', 'responsibilities', 'impact_description', 'learning_opportunities')
        }),
        ('Requirements', {
            'fields': ('requirements', 'skills_required', 'skills_preferred', 'skill_level')
        }),
        ('Logistics', {
            'fields': ('location', 'address', 'city', 'country', 'remote_allowed')
        }),
        ('Time Commitment', {
            'fields': ('time_commitment', 'duration_weeks', 'start_date', 'end_date', 'application_deadline')
        }),
        ('Capacity', {
            'fields': ('positions_available', 'positions_filled', 'min_age', 'max_age')
        }),
        ('Team & Supervision', {
            'fields': ('supervisor', 'team_lead', 'department'),
            'classes': ('collapse',)
        }),
        ('Support & Benefits', {
            'fields': ('training_provided', 'training_description', 'equipment_provided',
                      'equipment_description', 'certification_provided', 'certificate_name'),
            'classes': ('collapse',)
        }),
        ('Safety & Compliance', {
            'fields': ('safety_requirements', 'background_check_required', 
                      'background_check_type', 'liability_waiver_required'),
            'classes': ('collapse',)
        }),
        ('Media', {
            'fields': ('featured_image_preview', 'featured_image', 'gallery')
        }),
        ('SEO & Display', {
            'fields': ('is_featured', 'is_published', 'meta_title', 'meta_description')
        }),
        ('Statistics', {
            'fields': ('views', 'applications_count', 'completion_rate', 'volunteer_satisfaction',
                      'fill_percentage_display'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [VolunteerApplicationInline]
    
    def fill_percentage_display(self, obj):
        return f"{obj.fill_percentage():.1f}%"
    fill_percentage_display.short_description = 'Fill Percentage'
    
    def featured_image_preview(self, obj):
        if obj.featured_image:
            return format_html('<img src="{}" style="max-height: 150px; max-width: 200px;" />', 
                             obj.featured_image.url)
        return "No image"
    featured_image_preview.short_description = "Featured Image Preview"
    
    actions = ['publish_opportunities', 'feature_opportunities', 'calculate_fill_percentage']
    
    def publish_opportunities(self, request, queryset):
        updated = queryset.update(is_published=True, published_at=timezone.now())
        self.message_user(request, f'{updated} opportunities published.')
    publish_opportunities.short_description = "Publish selected opportunities"
    
    def feature_opportunities(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} opportunities featured.')
    feature_opportunities.short_description = "Feature selected opportunities"


class VolunteerTimeLogInline(admin.TabularInline):
    model = VolunteerTimeLog
    extra = 0
    fields = ('date', 'start_time', 'end_time', 'total_hours', 'status', 'approved_by')
    readonly_fields = ('approved_by',)
    can_delete = False
    max_num = 10


@admin.register(VolunteerApplication)
class VolunteerApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'opportunity', 'applicant', 'status', 'submitted_at', 
                   'review_score', 'background_check_status', 'training_status')
    list_filter = ('status', 'opportunity', 'availability_type', 'submitted_at', 
                  'background_check_status', 'training_status')
    search_fields = ('applicant__username', 'applicant__email', 'opportunity__title', 
                    'motivation_statement', 'emergency_contact_name')
    list_editable = ('status',)
    readonly_fields = ('uuid', 'submitted_at', 'reviewed_at', 'created_at', 
                      'updated_at', 'resume_preview', 'cover_letter_preview')
    raw_id_fields = ('opportunity', 'applicant', 'reviewer')
    date_hierarchy = 'submitted_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('opportunity', 'applicant', 'uuid', 'status')
        }),
        ('Application Details', {
            'fields': ('motivation_statement', 'relevant_experience', 'skills',
                      'availability_type', 'hours_per_week', 'start_date_preference')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone', 
                      'emergency_contact_relationship'),
            'classes': ('collapse',)
        }),
        ('Documents', {
            'fields': ('resume_preview', 'resume', 'cover_letter_preview', 'cover_letter',
                      'portfolio', 'additional_docs')
        }),
        ('Review Process', {
            'fields': ('reviewer', 'review_notes', 'review_score', 'reviewed_at',
                      'interview_scheduled', 'interview_notes', 'interview_score')
        }),
        ('Background Check', {
            'fields': ('background_check_status', 'background_check_completed_at'),
            'classes': ('collapse',)
        }),
        ('Training & Onboarding', {
            'fields': ('training_status', 'training_completed_at', 'onboarding_status'),
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
    
    def cover_letter_preview(self, obj):
        if obj.cover_letter:
            return format_html('<a href="{}" target="_blank">View Cover Letter</a>', 
                             obj.cover_letter.url)
        return "No cover letter"
    cover_letter_preview.short_description = "Cover Letter"
    
    actions = ['shortlist_applications', 'start_background_check', 'schedule_interviews']
    
    def shortlist_applications(self, request, queryset):
        updated = queryset.update(status='shortlisted')
        self.message_user(request, f'{updated} applications shortlisted.')
    shortlist_applications.short_description = "Shortlist selected applications"


@admin.register(VolunteerAssignment)
class VolunteerAssignmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'application', 'status', 'start_date', 'end_date', 
                   'hours_logged', 'tasks_completed', 'performance_rating', 
                   'certificate_issued')
    list_filter = ('status', 'start_date', 'certificate_issued')
    search_fields = ('application__applicant__username', 'application__opportunity__title', 
                    'supervisor__username', 'certificate_serial')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at', 'actual_start_date', 'actual_end_date')
    raw_id_fields = ('application', 'supervisor')
    filter_horizontal = ('team_members',)
    inlines = [VolunteerTimeLogInline]
    
    fieldsets = (
        ('Assignment Information', {
            'fields': ('application', 'status')
        }),
        ('Assignment Details', {
            'fields': ('start_date', 'end_date', 'expected_hours_per_week', 'work_schedule')
        }),
        ('Team', {
            'fields': ('supervisor', 'team_members')
        }),
        ('Actual Dates', {
            'fields': ('actual_start_date', 'actual_end_date'),
            'classes': ('collapse',)
        }),
        ('Performance Tracking', {
            'fields': ('hours_logged', 'tasks_completed', 'performance_rating', 'performance_notes')
        }),
        ('Resources', {
            'fields': ('equipment_assigned', 'access_provided'),
            'classes': ('collapse',)
        }),
        ('Certificates & Recognition', {
            'fields': ('certificate_issued', 'certificate_serial', 'issued_at', 'recognition_awards')
        }),
        ('Feedback', {
            'fields': ('volunteer_feedback', 'supervisor_feedback'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['issue_certificates', 'mark_as_completed', 'calculate_performance']
    
    def issue_certificates(self, request, queryset):
        for assignment in queryset.filter(certificate_issued=False):
            assignment.certificate_issued = True
            assignment.certificate_serial = f"VOL-{assignment.application.opportunity.slug}-{assignment.id}-{timezone.now().strftime('%Y%m%d')}"
            assignment.issued_at = timezone.now()
            assignment.save()
        self.message_user(request, f'Certificates issued for {queryset.count()} assignments.')
    issue_certificates.short_description = "Issue certificates to selected assignments"


@admin.register(VolunteerTimeLog)
class VolunteerTimeLogAdmin(admin.ModelAdmin):
    list_display = ('volunteer', 'assignment', 'date', 'start_time', 'end_time', 
                   'total_hours', 'status', 'approved_by', 'created_at')
    list_filter = ('status', 'date', 'remote_work', 'created_at')
    search_fields = ('volunteer__username', 'assignment__application__opportunity__title', 
                    'activity_description', 'project')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at', 'approved_at')
    raw_id_fields = ('assignment', 'volunteer', 'approved_by')
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('assignment', 'volunteer')
        }),
        ('Time Details', {
            'fields': ('date', 'start_time', 'end_time', 'total_hours', 'break_duration')
        }),
        ('Activity Details', {
            'fields': ('activity_description', 'tasks_completed', 'project')
        }),
        ('Status & Approval', {
            'fields': ('status', 'approved_by', 'approved_at', 'rejection_reason')
        }),
        ('Location', {
            'fields': ('location', 'remote_work'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes', 'challenges_faced', 'achievements'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_time_logs', 'reject_time_logs']
    
    def approve_time_logs(self, request, queryset):
        updated = queryset.update(
            status='approved',
            approved_by=request.user,
            approved_at=timezone.now()
        )
        self.message_user(request, f'{updated} time logs approved.')
    approve_time_logs.short_description = "Approve selected time logs"


@admin.register(VolunteerSkill)
class VolunteerSkillAdmin(admin.ModelAdmin):
    list_display = ('volunteer', 'skill_name', 'skill_level', 'years_experience', 
                   'verified', 'verified_by', 'times_utilized', 'last_used')
    list_filter = ('skill_level', 'verified', 'created_at')
    search_fields = ('volunteer__username', 'skill_name', 'certification')
    list_editable = ('verified', 'skill_level')
    readonly_fields = ('created_at', 'updated_at', 'verified_at')
    raw_id_fields = ('volunteer', 'verified_by')
    
    fieldsets = (
        ('Skill Information', {
            'fields': ('volunteer', 'skill_name', 'skill_level', 'years_experience', 'certification')
        }),
        ('Verification', {
            'fields': ('verified', 'verified_by', 'verified_at')
        }),
        ('Usage', {
            'fields': ('times_utilized', 'last_used'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['verify_skills', 'update_usage_stats']
    
    def verify_skills(self, request, queryset):
        updated = queryset.update(
            verified=True,
            verified_by=request.user,
            verified_at=timezone.now()
        )
        self.message_user(request, f'{updated} skills verified.')
    verify_skills.short_description = "Verify selected skills"


@admin.register(VolunteerAward)
class VolunteerAwardAdmin(admin.ModelAdmin):
    list_display = ('title', 'volunteer', 'award_type', 'issued_by', 'issued_at', 
                   'valid_until', 'is_public', 'verification_code')
    list_filter = ('award_type', 'is_public', 'issued_at')
    search_fields = ('title', 'volunteer__username', 'description', 'verification_code')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('volunteer', 'issued_by')
    date_hierarchy = 'issued_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('volunteer', 'award_type', 'title', 'description')
        }),
        ('Details', {
            'fields': ('issued_by', 'issued_at', 'valid_until')
        }),
        ('Media', {
            'fields': ('certificate_file', 'badge_image', 'badge_url')
        }),
        ('Verification & Visibility', {
            'fields': ('verification_code', 'is_public')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(VolunteerEvent)
class VolunteerEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'start_datetime', 'end_datetime', 
                   'location_type', 'current_attendees', 'max_attendees', 
                   'is_published', 'attendance_rate')
    list_filter = ('event_type', 'location_type', 'is_published', 'is_cancelled', 'start_datetime')
    search_fields = ('title', 'description', 'location')
    list_editable = ('is_published',)
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ()
    filter_horizontal = ('organizers', 'presenters')
    date_hierarchy = 'start_datetime'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'event_type')
        }),
        ('Timing', {
            'fields': ('start_datetime', 'end_datetime', 'timezone')
        }),
        ('Location', {
            'fields': ('location_type', 'location', 'online_link')
        }),
        ('Audience & Registration', {
            'fields': ('target_audience', 'max_attendees', 'current_attendees',
                      'registration_required', 'registration_deadline')
        }),
        ('Team', {
            'fields': ('organizers', 'presenters')
        }),
        ('Content', {
            'fields': ('resources', 'agenda'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_published', 'is_cancelled')
        }),
        ('Statistics', {
            'fields': ('attendance_rate', 'satisfaction_rating'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )