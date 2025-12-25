from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.urls import path
from django.shortcuts import render, redirect
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
import json

from .models import (
    BlogCategory, BlogTag, BlogPost, BlogComment,
    BlogLike, NewsletterPost, BlogView, BlogSeries
)


class BlogCommentInline(admin.TabularInline):
    model = BlogComment
    extra = 0
    fields = ('get_author_name', 'content_preview', 'status', 'created_at')
    readonly_fields = ('get_author_name', 'content_preview', 'created_at')
    can_delete = False
    max_num = 5
    
    def get_author_name(self, obj):
        return obj.get_author_name()
    get_author_name.short_description = 'Author'
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content'


class BlogLikeInline(admin.TabularInline):
    model = BlogLike
    extra = 0
    fields = ('user', 'ip_address', 'created_at')
    readonly_fields = ('user', 'ip_address', 'created_at')
    can_delete = False
    max_num = 5


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'display_order', 'post_count', 'is_active')
    list_editable = ('display_order', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    
    actions = ['recalculate_post_counts']
    
    def recalculate_post_counts(self, request, queryset):
        for category in queryset:
            category.update_post_count()
        self.message_user(request, 'Post counts recalculated.')
    recalculate_post_counts.short_description = "Recalculate post counts"


@admin.register(BlogTag)
class BlogTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'post_count', 'description_preview')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    
    def description_preview(self, obj):
        return obj.description[:100] + '...' if len(obj.description) > 100 else obj.description
    description_preview.short_description = 'Description'
    
    actions = ['recalculate_post_counts']
    
    def recalculate_post_counts(self, request, queryset):
        for tag in queryset:
            tag.update_post_count()
        self.message_user(request, 'Post counts recalculated.')
    recalculate_post_counts.short_description = "Recalculate post counts"


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'status', 'is_featured', 
                   'published_at', 'views', 'likes', 'comment_count')
    list_filter = ('category', 'status', 'content_type', 'is_featured', 
                  'allow_comments', 'published_at', 'created_at')
    search_fields = ('title', 'excerpt', 'content', 'slug')
    list_editable = ('is_featured', 'status')
    readonly_fields = ('uuid', 'views', 'likes', 'comment_count', 'word_count', 
                      'read_time_minutes', 'created_at', 'updated_at', 'published_at',
                      'featured_image_preview')
    raw_id_fields = ('author', 'editor', 'last_modified_by')
    filter_horizontal = ('tags', 'co_authors', 'related_posts', 'related_programs',
                        'related_publications', 'related_projects')
    date_hierarchy = 'published_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'uuid', 'excerpt', 'content', 'content_type')
        }),
        ('Categorization', {
            'fields': ('category', 'tags', 'related_posts')
        }),
        ('Authorship', {
            'fields': ('author', 'co_authors', 'editor')
        }),
        ('Media', {
            'fields': ('featured_image_preview', 'featured_image', 'image_caption', 
                      'image_credit', 'gallery', 'video_url')
        }),
        ('Publication Status', {
            'fields': ('status', 'is_featured', 'is_pinned', 'allow_comments',
                      'published_at', 'scheduled_at')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords', 'canonical_url'),
            'classes': ('collapse',)
        }),
        ('Social Sharing', {
            'fields': ('social_image', 'social_title', 'social_description'),
            'classes': ('collapse',)
        }),
        ('Reading Experience', {
            'fields': ('word_count', 'read_time_minutes'),
            'classes': ('collapse',)
        }),
        ('Related Content', {
            'fields': ('related_programs', 'related_publications', 'related_projects'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('views', 'likes', 'shares', 'comment_count'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'last_modified_by'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [BlogCommentInline, BlogLikeInline]
    
    def featured_image_preview(self, obj):
        if obj.featured_image:
            return format_html('<img src="{}" style="max-height: 150px; max-width: 200px;" />', 
                             obj.featured_image.url)
        return "No image"
    featured_image_preview.short_description = "Featured Image Preview"
    
    actions = ['publish_posts', 'feature_posts', 'export_posts', 'calculate_read_time']
    
    def publish_posts(self, request, queryset):
        updated = queryset.update(status='published', published_at=timezone.now())
        self.message_user(request, f'{updated} posts published.')
    publish_posts.short_description = "Publish selected posts"
    
    def feature_posts(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} posts featured.')
    feature_posts.short_description = "Feature selected posts"
    
    def calculate_read_time(self, request, queryset):
        for post in queryset:
            post.save()  # Triggers read time calculation in save method
        self.message_user(request, 'Read times calculated.')
    calculate_read_time.short_description = "Calculate read time"
    
    def changelist_view(self, request, extra_context=None):
        # Add stats to changelist
        stats = {
            'total_posts': BlogPost.objects.count(),
            'published_posts': BlogPost.objects.filter(status='published').count(),
            'draft_posts': BlogPost.objects.filter(status='draft').count(),
            'scheduled_posts': BlogPost.objects.filter(status='scheduled').count(),
            'total_views': BlogPost.objects.aggregate(total=Sum('views'))['total'] or 0,
            'total_comments': BlogPost.objects.aggregate(total=Sum('comment_count'))['total'] or 0,
        }
        extra_context = extra_context or {}
        extra_context['stats'] = stats
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ('get_author_name', 'post', 'content_preview', 'status', 
                   'created_at', 'approved_at')
    list_filter = ('status', 'created_at', 'approved_at', 'is_edited')
    search_fields = ('content', 'guest_name', 'guest_email', 'post__title')
    list_editable = ('status',)
    readonly_fields = ('ip_address', 'user_agent', 'created_at', 'updated_at', 'approved_at')
    raw_id_fields = ('post', 'author', 'parent', 'moderated_by')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Comment Information', {
            'fields': ('post', 'parent')
        }),
        ('Commenter Information', {
            'fields': ('author', 'guest_name', 'guest_email', 'guest_website')
        }),
        ('Content', {
            'fields': ('content', 'is_edited', 'edit_reason')
        }),
        ('Status and Moderation', {
            'fields': ('status', 'moderated_by', 'moderation_notes')
        }),
        ('Engagement', {
            'fields': ('likes', 'dislikes'),
            'classes': ('collapse',)
        }),
        ('Technical Details', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'approved_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_author_name(self, obj):
        return obj.get_author_name()
    get_author_name.short_description = 'Author'
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content'
    
    actions = ['approve_comments', 'mark_as_spam', 'delete_spam']
    
    def approve_comments(self, request, queryset):
        updated = queryset.update(status='approved', approved_at=timezone.now())
        self.message_user(request, f'{updated} comments approved.')
    approve_comments.short_description = "Approve selected comments"
    
    def mark_as_spam(self, request, queryset):
        updated = queryset.update(status='spam')
        self.message_user(request, f'{updated} comments marked as spam.')
    mark_as_spam.short_description = "Mark as spam"
    
    def delete_spam(self, request, queryset):
        count, _ = queryset.filter(status='spam').delete()
        self.message_user(request, f'{count} spam comments deleted.')
    delete_spam.short_description = "Delete spam comments"


@admin.register(BlogLike)
class BlogLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'ip_address', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'post__title', 'ip_address')
    readonly_fields = ('user', 'post', 'ip_address', 'user_agent', 'created_at')
    raw_id_fields = ('user', 'post')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(BlogView)
class BlogViewAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'ip_address', 'time_on_page', 'scroll_depth', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('post__title', 'user__username', 'ip_address')
    readonly_fields = ('post', 'user', 'ip_address', 'user_agent', 'referrer', 
                      'session_id', 'time_on_page', 'scroll_depth', 'created_at')
    raw_id_fields = ('post', 'user')
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(NewsletterPost)
class NewsletterPostAdmin(admin.ModelAdmin):
    list_display = ('post', 'newsletter_id', 'sent_at', 'open_count', 'click_count', 'unsubscribe_count')
    list_filter = ('sent_at',)
    search_fields = ('post__title', 'newsletter_id')
    readonly_fields = ('post', 'newsletter_id', 'sent_at', 'open_count', 'click_count', 'unsubscribe_count')
    raw_id_fields = ('post',)
    
    def has_add_permission(self, request):
        return False


@admin.register(BlogSeries)
class BlogSeriesAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_active', 'display_order', 'post_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'description')
    list_editable = ('is_active', 'display_order')
    filter_horizontal = ('posts',)
    readonly_fields = ('created_at', 'updated_at')
    
    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = 'Posts'