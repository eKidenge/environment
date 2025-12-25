from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import path
from django.utils import timezone
import json

from .models import (
    SiteConfiguration, TeamMember, ImpactMetric, 
    FAQ, SitePage, NewsletterSubscription
)

@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'contact_email', 'maintenance_mode', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('site_name', 'tagline', 'mission_statement', 'vision_statement')
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'contact_phone', 'contact_address')
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'twitter_url', 'instagram_url', 
                      'linkedin_url', 'youtube_url', 'github_url'),
            'classes': ('collapse',)
        }),
        ('Site Settings', {
            'fields': ('maintenance_mode', 'allow_registrations', 'allow_comments')
        }),
        ('SEO Settings', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': ('google_analytics_id', 'facebook_pixel_id'),
            'classes': ('collapse',)
        }),
        ('File Uploads', {
            'fields': ('max_upload_size_mb', 'allowed_file_types'),
            'classes': ('collapse',)
        }),
        ('Email Configuration', {
            'fields': ('email_host', 'email_port', 'email_use_tls',
                      'email_host_user', 'email_host_password'),
            'classes': ('collapse',)
        }),
        ('Cache Settings', {
            'fields': ('cache_timeout',),
            'classes': ('collapse',)
        }),
        ('Feature Flags', {
            'fields': ('enable_blog', 'enable_forum', 'enable_shop', 'enable_donations'),
            'classes': ('collapse',)
        }),
        ('Theme Settings', {
            'fields': ('primary_color', 'secondary_color', 'accent_color'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return not SiteConfiguration.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def changelist_view(self, request, extra_context=None):
        if SiteConfiguration.objects.exists():
            obj = SiteConfiguration.objects.first()
            return redirect('admin:core_siteconfiguration_change', object_id=obj.pk)
        return super().changelist_view(request, extra_context)


class TeamMemberInline(admin.TabularInline):
    model = TeamMember
    extra = 1
    fields = ('user', 'role', 'department', 'is_active', 'show_on_website')
    raw_id_fields = ('user',)


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'department', 'is_active', 'show_on_website', 'display_order')
    list_filter = ('role', 'department', 'is_active', 'show_on_website', 'is_leadership')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'department')
    list_editable = ('display_order', 'is_active', 'show_on_website')
    raw_id_fields = ('user',)
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'uuid', 'role', 'department', 'bio')
        }),
        ('Expertise & Stats', {
            'fields': ('expertise', 'years_with_yes', 'projects_led'),
            'classes': ('collapse',)
        }),
        ('Display Settings', {
            'fields': ('display_order', 'is_active', 'is_leadership', 'show_on_website')
        }),
        ('Social Media', {
            'fields': ('team_twitter', 'team_linkedin', 'team_website'),
            'classes': ('collapse',)
        }),
        ('Media', {
            'fields': ('profile_image_preview', 'profile_image', 'cover_image_preview', 'cover_image'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def profile_image_preview(self, obj):
        if obj.profile_image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px;" />', 
                             obj.profile_image.url)
        return "No image"
    profile_image_preview.short_description = "Profile Image Preview"
    
    def cover_image_preview(self, obj):
        if obj.cover_image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 200px;" />', 
                             obj.cover_image.url)
        return "No image"
    cover_image_preview.short_description = "Cover Image Preview"


@admin.register(ImpactMetric)
class ImpactMetricAdmin(admin.ModelAdmin):
    list_display = ('name', 'metric_type', 'current_value', 'unit', 
                   'target_value', 'is_public', 'display_order')
    list_filter = ('metric_type', 'is_public')
    search_fields = ('name', 'description', 'unit')
    list_editable = ('display_order', 'is_public', 'current_value')
    readonly_fields = ('created_at', 'updated_at', 'progress_percentage')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'metric_type', 'description', 'unit', 'icon')
        }),
        ('Measurement Values', {
            'fields': ('current_value', 'baseline_value', 'target_value', 'progress_percentage')
        }),
        ('Calculation & Data', {
            'fields': ('calculation_formula', 'data_source', 'update_frequency'),
            'classes': ('collapse',)
        }),
        ('Visualization', {
            'fields': ('chart_type', 'display_color', 'display_order', 'is_public')
        }),
        ('History', {
            'fields': ('history',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('last_updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def progress_percentage(self, obj):
        progress = obj.calculate_progress()
        return f"{progress:.1f}%"
    progress_percentage.short_description = "Progress"
    
    def save_model(self, request, obj, form, change):
        if change:
            obj.last_updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question_short', 'category', 'is_published', 'is_featured', 
                   'display_order', 'views', 'helpful_score')
    list_filter = ('category', 'is_published', 'is_featured', 'created_at')
    search_fields = ('question', 'answer')
    list_editable = ('display_order', 'is_published', 'is_featured')
    filter_horizontal = ('related_faqs',)
    readonly_fields = ('views', 'helpful_yes', 'helpful_no', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Content', {
            'fields': ('question', 'answer', 'category', 'slug')
        }),
        ('Display Settings', {
            'fields': ('display_order', 'is_published', 'is_featured')
        }),
        ('Stats', {
            'fields': ('views', 'helpful_yes', 'helpful_no'),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Related FAQs', {
            'fields': ('related_faqs',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def question_short(self, obj):
        return obj.question[:100] + '...' if len(obj.question) > 100 else obj.question
    question_short.short_description = 'Question'
    
    def helpful_score(self, obj):
        total = obj.helpful_yes + obj.helpful_no
        if total > 0:
            score = (obj.helpful_yes / total) * 100
            return f"{score:.0f}%"
        return "0%"
    helpful_score.short_description = 'Helpful Score'
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SitePage)
class SitePageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'page_type', 'is_published', 'show_in_navigation', 
                   'navigation_order', 'parent', 'views')
    list_filter = ('page_type', 'is_published', 'show_in_navigation', 'created_at')
    search_fields = ('title', 'slug', 'content', 'excerpt')
    list_editable = ('navigation_order', 'is_published', 'show_in_navigation')
    readonly_fields = ('views', 'created_at', 'updated_at', 'featured_image_preview')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'page_type')
        }),
        ('Content', {
            'fields': ('excerpt', 'content')
        }),
        ('Media', {
            'fields': ('featured_image_preview', 'featured_image')
        }),
        ('Settings', {
            'fields': ('is_published', 'is_featured', 'show_in_navigation', 
                      'navigation_order', 'require_authentication')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords', 'canonical_url'),
            'classes': ('collapse',)
        }),
        ('Template & Structure', {
            'fields': ('template_name', 'parent'),
            'classes': ('collapse',)
        }),
        ('Stats', {
            'fields': ('views',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def featured_image_preview(self, obj):
        if obj.featured_image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 200px;" />', 
                             obj.featured_image.url)
        return "No image"
    featured_image_preview.short_description = "Featured Image Preview"
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'is_active', 'is_verified', 'frequency', 
                   'subscribed_at', 'emails_sent', 'open_rate', 'click_rate')
    list_filter = ('is_active', 'is_verified', 'frequency', 'subscribed_at')
    search_fields = ('email', 'name')
    readonly_fields = ('verification_token', 'subscribed_at', 'verified_at', 
                      'unsubscribed_at', 'last_email_sent', 'ip_address')
    
    fieldsets = (
        ('Subscriber Information', {
            'fields': ('email', 'name')
        }),
        ('Preferences', {
            'fields': ('categories', 'frequency')
        }),
        ('Status', {
            'fields': ('is_active', 'is_verified', 'verification_token')
        }),
        ('Statistics', {
            'fields': ('emails_sent', 'emails_opened', 'emails_clicked'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'subscribed_at', 'verified_at', 
                      'unsubscribed_at', 'last_email_sent'),
            'classes': ('collapse',)
        }),
    )
    
    def open_rate(self, obj):
        if obj.emails_sent > 0:
            rate = (obj.emails_opened / obj.emails_sent) * 100
            return f"{rate:.1f}%"
        return "0%"
    open_rate.short_description = 'Open Rate'
    
    def click_rate(self, obj):
        if obj.emails_sent > 0:
            rate = (obj.emails_clicked / obj.emails_sent) * 100
            return f"{rate:.1f}%"
        return "0%"
    click_rate.short_description = 'Click Rate'
    
    actions = ['verify_subscriptions', 'unsubscribe_selected', 'export_subscriptions']
    
    def verify_subscriptions(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} subscriptions verified.')
    verify_subscriptions.short_description = "Verify selected subscriptions"
    
    def unsubscribe_selected(self, request, queryset):
        updated = queryset.update(is_active=False, unsubscribed_at=timezone.now())
        self.message_user(request, f'{updated} subscriptions unsubscribed.')
    unsubscribe_selected.short_description = "Unsubscribe selected"