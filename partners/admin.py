from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.utils import timezone

from .models import (
    PartnerOrganization, PartnershipAgreement, PartnershipProject,
    PartnerContact, PartnershipMeeting, PartnershipResource,
    PartnerEvaluation, PartnershipOpportunity
)


class PartnershipAgreementInline(admin.TabularInline):
    model = PartnershipAgreement
    extra = 0
    fields = ('agreement_number', 'agreement_title', 'effective_date', 'status')
    readonly_fields = ('agreement_number',)
    can_delete = False
    max_num = 3


class PartnerContactInline(admin.TabularInline):
    model = PartnerContact
    extra = 1
    fields = ('first_name', 'last_name', 'position', 'email', 'phone', 'is_primary', 'is_active')
    show_change_link = True


class PartnershipProjectInline(admin.TabularInline):
    model = PartnershipProject
    extra = 0
    fields = ('title', 'status', 'start_date', 'budget')
    readonly_fields = ('start_date', 'budget')
    can_delete = False
    max_num = 3


@admin.register(PartnerOrganization)
class PartnerOrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization_type', 'partnership_level', 'status', 
                   'country', 'partnership_start', 'total_funding', 'is_featured', 
                   'is_public', 'show_on_website')
    list_filter = ('organization_type', 'partnership_level', 'status', 'country', 
                  'is_featured', 'is_public', 'show_on_website', 'partnership_start')
    search_fields = ('name', 'description', 'contact_person', 'city', 'country', 
                    'focus_areas', 'collaboration_areas', 'slug')
    list_editable = ('is_featured', 'status', 'is_public', 'show_on_website')
    readonly_fields = ('uuid', 'created_at', 'updated_at', 'verified_at', 
                      'total_contribution_value_display', 'partnership_duration_display',
                      'logo_preview', 'cover_image_preview')
    raw_id_fields = ('focal_point', 'verified_by')
    filter_horizontal = ()
    date_hierarchy = 'partnership_start'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'uuid', 'organization_type', 'partnership_level', 'status')
        }),
        ('Organization Details', {
            'fields': ('description', 'mission', 'vision', 'values', 'focus_areas')
        }),
        ('Contact Information', {
            'fields': ('website', 'primary_email', 'primary_phone', 'secondary_email', 'secondary_phone')
        }),
        ('Location', {
            'fields': ('headquarters', 'country', 'region', 'city', 'operating_countries')
        }),
        ('Organization Stats', {
            'fields': ('founded_year', 'employee_count', 'annual_budget', 'budget_currency'),
            'classes': ('collapse',)
        }),
        ('Key People', {
            'fields': ('contact_person', 'contact_position', 'contact_email', 'contact_phone',
                      'focal_point', 'decision_maker', 'decision_maker_position')
        }),
        ('Media', {
            'fields': ('logo_preview', 'logo', 'logo_white', 'cover_image_preview', 'cover_image', 'brand_assets')
        }),
        ('Partnership Details', {
            'fields': ('partnership_start', 'partnership_end', 'agreement_document', 
                      'agreement_version', 'agreement_status')
        }),
        ('Collaboration Areas', {
            'fields': ('collaboration_areas', 'joint_projects', 'expertise_shared', 'resources_shared'),
            'classes': ('collapse',)
        }),
        ('Financial Contributions', {
            'fields': ('total_funding', 'funding_currency', 'funding_breakdown', 
                      'in_kind_contributions', 'in_kind_value', 'total_contribution_value_display')
        }),
        ('Impact & Metrics', {
            'fields': ('people_reached', 'impact_stories', 'success_metrics'),
            'classes': ('collapse',)
        }),
        ('Communication & Reporting', {
            'fields': ('communication_frequency', 'last_communication', 'next_communication',
                      'reporting_requirements', 'report_frequency'),
            'classes': ('collapse',)
        }),
        ('Strategic Alignment', {
            'fields': ('sdg_alignment', 'strategic_fit', 'risk_assessment', 'risk_level'),
            'classes': ('collapse',)
        }),
        ('Social Media & Online Presence', {
            'fields': ('social_media', 'press_mentions', 'publications'),
            'classes': ('collapse',)
        }),
        ('Internal Assessment', {
            'fields': ('internal_notes', 'strengths', 'weaknesses', 'opportunities', 
                      'threats', 'partner_score'),
            'classes': ('collapse',)
        }),
        ('Visibility & Display', {
            'fields': ('is_featured', 'is_public', 'display_order', 'show_on_website',
                      'meta_title', 'meta_description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'verified_at', 'verified_by'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [PartnershipAgreementInline, PartnerContactInline, PartnershipProjectInline]
    
    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px;" />', 
                             obj.logo.url)
        return "No logo"
    logo_preview.short_description = "Logo Preview"
    
    def cover_image_preview(self, obj):
        if obj.cover_image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 200px;" />', 
                             obj.cover_image.url)
        return "No cover image"
    cover_image_preview.short_description = "Cover Image Preview"
    
    def total_contribution_value_display(self, obj):
        return f"${obj.total_contribution_value():,.2f}"
    total_contribution_value_display.short_description = 'Total Contribution Value'
    
    def partnership_duration_display(self, obj):
        years = obj.partnership_duration()
        return f"{years} year(s)" if years else "N/A"
    partnership_duration_display.short_description = 'Partnership Duration'
    
    actions = ['feature_partners', 'activate_partnerships', 'archive_partners']
    
    def feature_partners(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} partners featured.')
    feature_partners.short_description = "Feature selected partners"
    
    def activate_partnerships(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} partnerships activated.')
    activate_partnerships.short_description = "Activate selected partnerships"


@admin.register(PartnershipAgreement)
class PartnershipAgreementAdmin(admin.ModelAdmin):
    list_display = ('agreement_number', 'partner', 'agreement_title', 'effective_date', 
                   'expiration_date', 'status', 'financial_commitment', 'signed_date')
    list_filter = ('status', 'effective_date', 'expiration_date')  # REMOVED: 'agreement_status'
    search_fields = ('agreement_number', 'agreement_title', 'partner__name', 'purpose')
    readonly_fields = ('created_at', 'updated_at', 'agreement_document_preview')
    raw_id_fields = ('partner', 'our_signatory', 'created_by')
    date_hierarchy = 'effective_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('partner', 'agreement_title', 'agreement_number', 'version')
        }),
        ('Content', {
            'fields': ('purpose', 'objectives', 'scope', 'deliverables', 'responsibilities')
        }),
        ('Terms', {
            'fields': ('effective_date', 'expiration_date', 'renewal_terms', 'termination_clause')
        }),
        ('Financial Terms', {
            'fields': ('financial_commitment', 'payment_schedule', 'in_kind_commitments'),
            'classes': ('collapse',)
        }),
        ('Legal', {
            'fields': ('governing_law', 'jurisdiction', 'confidentiality', 'intellectual_property'),
            'classes': ('collapse',)
        }),
        ('Documents', {
            'fields': ('agreement_document_preview', 'agreement_document', 'annexes', 'amendments')
        }),
        ('Signatories', {
            'fields': ('our_signatory', 'partner_signatory_name', 'partner_signatory_position', 'signed_date')
        }),
        ('Status', {
            'fields': ('status', 'compliance_status', 'compliance_notes')
        }),
        ('Review Schedule', {
            'fields': ('last_review_date', 'next_review_date'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def agreement_document_preview(self, obj):
        if obj.agreement_document:
            return format_html('<a href="{}" target="_blank">View Agreement</a>', 
                             obj.agreement_document.url)
        return "No document"
    agreement_document_preview.short_description = "Agreement Document"


@admin.register(PartnershipProject)
class PartnershipProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'partner', 'program', 'status', 'start_date', 'end_date', 
                   'budget', 'is_featured', 'is_public')
    list_filter = ('status', 'thematic_areas', 'start_date', 'is_featured', 'is_public')
    search_fields = ('title', 'description', 'partner__name', 'program__title')
    list_editable = ('status', 'is_featured', 'is_public')
    readonly_fields = ('created_at', 'updated_at', 'featured_image_preview', 
                      'case_study_preview')
    raw_id_fields = ('partner', 'program', 'research_project', 'project_lead', 'created_by')
    filter_horizontal = ('team_members',)
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'partner', 'program', 'research_project', 'description', 'objectives')
        }),
        ('Scope', {
            'fields': ('geographic_scope', 'thematic_areas', 'target_audience'),
            'classes': ('collapse',)
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date', 'status')
        }),
        ('Resources', {
            'fields': ('budget', 'partner_contribution', 'yes_contribution', 'in_kind_contributions')
        }),
        ('Team', {
            'fields': ('project_lead', 'partner_lead', 'team_members')
        }),
        ('Deliverables & Milestones', {
            'fields': ('deliverables', 'milestones'),
            'classes': ('collapse',)
        }),
        ('Impact', {
            'fields': ('expected_impact', 'success_metrics', 'actual_results'),
            'classes': ('collapse',)
        }),
        ('Media', {
            'fields': ('featured_image_preview', 'featured_image', 'gallery', 
                      'case_study_preview', 'case_study')
        }),
        ('Communication', {
            'fields': ('communication_plan', 'reporting_requirements'),
            'classes': ('collapse',)
        }),
        ('Evaluation', {
            'fields': ('lessons_learned', 'recommendations', 'sustainability_plan'),
            'classes': ('collapse',)
        }),
        ('Visibility', {
            'fields': ('is_featured', 'is_public')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def featured_image_preview(self, obj):
        if obj.featured_image:
            return format_html('<img src="{}" style="max-height: 150px; max-width: 200px;" />', 
                             obj.featured_image.url)
        return "No image"
    featured_image_preview.short_description = "Featured Image Preview"
    
    def case_study_preview(self, obj):
        if obj.case_study:
            return format_html('<a href="{}" target="_blank">View Case Study</a>', 
                             obj.case_study.url)
        return "No case study"
    case_study_preview.short_description = "Case Study"


@admin.register(PartnerContact)
class PartnerContactAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'partner', 'position', 'email', 'phone', 
                   'decision_making_level', 'is_primary', 'is_active', 'last_contact')
    list_filter = ('is_primary', 'is_active', 'decision_making_level', 'department', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'partner__name', 'position')
    list_editable = ('is_primary', 'is_active')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('partner', 'added_by')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('partner', 'first_name', 'last_name', 'position', 'department')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'mobile', 'whatsapp')
        }),
        ('Communication Preferences', {
            'fields': ('preferred_contact_method', 'preferred_contact_time', 'language_preference')
        }),
        ('Role in Partnership', {
            'fields': ('role', 'decision_making_level', 'relationship_strength')
        }),
        ('Relationship Management', {
            'fields': ('last_contact', 'next_contact', 'notes'),
            'classes': ('collapse',)
        }),
        ('Social Media', {
            'fields': ('linkedin', 'twitter'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_primary')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'added_by'),
            'classes': ('collapse',)
        }),
    )
    
    def full_name(self, obj):
        return obj.full_name()
    full_name.short_description = 'Name'


@admin.register(PartnershipMeeting)
class PartnershipMeetingAdmin(admin.ModelAdmin):
    list_display = ('title', 'partner', 'project', 'scheduled_date', 'scheduled_time', 
                   'meeting_type', 'status', 'duration')
    list_filter = ('meeting_type', 'status', 'scheduled_date')
    search_fields = ('title', 'purpose', 'partner__name', 'project__title')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at', 'minutes_document_preview')
    raw_id_fields = ('partner', 'project', 'created_by')
    filter_horizontal = ('yes_team',)
    date_hierarchy = 'scheduled_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('partner', 'project', 'title', 'purpose', 'agenda')
        }),
        ('Timing', {
            'fields': ('scheduled_date', 'scheduled_time', 'duration', 'timezone')
        }),
        ('Location/Platform', {
            'fields': ('meeting_type', 'location', 'meeting_link', 'dial_in_info')
        }),
        ('Participants', {
            'fields': ('yes_team', 'partner_team')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Follow-up', {
            'fields': ('decisions_made', 'action_items', 'next_steps', 'meeting_notes',
                      'minutes_document_preview', 'minutes_document')
        }),
        ('Feedback', {
            'fields': ('satisfaction_rating', 'feedback'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def minutes_document_preview(self, obj):
        if obj.minutes_document:
            return format_html('<a href="{}" target="_blank">View Minutes</a>', 
                             obj.minutes_document.url)
        return "No minutes"
    minutes_document_preview.short_description = "Meeting Minutes"


@admin.register(PartnershipResource)
class PartnershipResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'partner', 'project', 'resource_type', 'direction', 
                   'confidentiality_level', 'download_count', 'created_at')
    list_filter = ('resource_type', 'direction', 'confidentiality_level', 'created_at')
    search_fields = ('title', 'description', 'partner__name', 'project__title', 'tags')
    readonly_fields = ('download_count', 'view_count', 'created_at', 'updated_at', 
                      'file_preview')
    raw_id_fields = ('partner', 'project', 'uploaded_by')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('partner', 'project', 'resource_type', 'direction', 'title', 'description')
        }),
        ('Content', {
            'fields': ('file_preview', 'file', 'url')
        }),
        ('Metadata', {
            'fields': ('version', 'language', 'tags')
        }),
        ('Access & Usage', {
            'fields': ('confidentiality_level', 'usage_terms', 'expiration_date')
        }),
        ('Statistics', {
            'fields': ('download_count', 'view_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'uploaded_by'),
            'classes': ('collapse',)
        }),
    )
    
    def file_preview(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">View File</a>', obj.file.url)
        return "No file"
    file_preview.short_description = "File"


@admin.register(PartnerEvaluation)
class PartnerEvaluationAdmin(admin.ModelAdmin):
    list_display = ('partner', 'evaluation_period_start', 'evaluation_period_end', 
                   'evaluation_date', 'rating_overall', 'average_rating_display', 
                   'continue_partnership', 'is_finalized', 'shared_with_partner')
    list_filter = ('is_finalized', 'shared_with_partner', 'evaluation_date')
    search_fields = ('partner__name', 'strengths', 'areas_for_improvement', 'specific_recommendations')
    readonly_fields = ('created_at', 'updated_at', 'finalized_at', 'shared_date', 
                      'average_rating_display', 'evaluation_report_preview')
    raw_id_fields = ('partner', 'evaluated_by')
    date_hierarchy = 'evaluation_date'
    
    fieldsets = (
        ('Evaluation Information', {
            'fields': ('partner', 'evaluated_by', 'evaluation_period_start', 
                      'evaluation_period_end', 'evaluation_date')
        }),
        ('Ratings (1-5 Scale)', {
            'fields': ('rating_strategic_alignment', 'rating_communication', 'rating_reliability',
                      'rating_value_added', 'rating_innovation', 'rating_overall', 'average_rating_display')
        }),
        ('Qualitative Assessment', {
            'fields': ('strengths', 'areas_for_improvement', 'key_achievements', 'challenges_faced')
        }),
        ('Recommendations', {
            'fields': ('continue_partnership', 'partnership_level_recommendation', 'specific_recommendations')
        }),
        ('Impact Assessment', {
            'fields': ('impact_on_yes', 'impact_on_partner', 'mutual_benefits'),
            'classes': ('collapse',)
        }),
        ('Documents', {
            'fields': ('evaluation_report_preview', 'evaluation_report', 'supporting_documents')
        }),
        ('Status', {
            'fields': ('is_finalized', 'finalized_at', 'shared_with_partner', 'shared_date', 'partner_feedback')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def average_rating_display(self, obj):
        return f"{obj.average_rating():.2f}"
    average_rating_display.short_description = 'Average Rating'
    
    def evaluation_report_preview(self, obj):
        if obj.evaluation_report:
            return format_html('<a href="{}" target="_blank">View Report</a>', 
                             obj.evaluation_report.url)
        return "No report"
    evaluation_report_preview.short_description = "Evaluation Report"


@admin.register(PartnershipOpportunity)
class PartnershipOpportunityAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization_name', 'potential_partnership_level', 
                   'status', 'probability', 'priority', 'identified_date', 
                   'target_close_date', 'assigned_to')
    list_filter = ('status', 'priority', 'potential_partnership_level', 'source_type', 'identified_date')
    search_fields = ('name', 'description', 'organization_name', 'contact_name', 'source')
    list_editable = ('status', 'probability', 'priority')
    readonly_fields = ('created_at', 'updated_at', 'actual_close_date')
    raw_id_fields = ('assigned_to', 'converted_partner', 'created_by')
    filter_horizontal = ('team_members',)
    date_hierarchy = 'identified_date'
    
    fieldsets = (
        ('Opportunity Details', {
            'fields': ('name', 'description', 'organization_name', 'organization_type')
        }),
        ('Potential Partnership', {
            'fields': ('potential_partnership_level', 'potential_value', 'potential_areas')
        }),
        ('Source', {
            'fields': ('source', 'source_type')
        }),
        ('Contact', {
            'fields': ('contact_name', 'contact_email', 'contact_phone')
        }),
        ('Status Tracking', {
            'fields': ('status', 'probability', 'priority')
        }),
        ('Timeline', {
            'fields': ('identified_date', 'target_close_date', 'actual_close_date')
        }),
        ('Team', {
            'fields': ('assigned_to', 'team_members')
        }),
        ('Strategy & Notes', {
            'fields': ('notes', 'strategy', 'challenges'),
            'classes': ('collapse',)
        }),
        ('Outcome', {
            'fields': ('outcome', 'outcome_reason', 'lessons_learned', 'converted_partner'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['convert_to_partner', 'update_probabilities']
    
    def convert_to_partner(self, request, queryset):
        for opportunity in queryset.filter(status='won', converted_partner__isnull=True):
            # Create a new partner from the opportunity
            partner = PartnerOrganization.objects.create(
                name=opportunity.organization_name or opportunity.name,
                organization_type=opportunity.organization_type,
                partnership_level=opportunity.potential_partnership_level,
                status='prospect',
                description=opportunity.description,
                contact_person=opportunity.contact_name,
                contact_email=opportunity.contact_email or '',
                created_by=request.user
            )
            opportunity.converted_partner = partner
            opportunity.save()
        
        self.message_user(request, f'{queryset.count()} opportunities converted to partners.')
    convert_to_partner.short_description = "Convert selected opportunities to partners"