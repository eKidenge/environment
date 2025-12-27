from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from.models import CustomUser, UserActivityLog, UserVerification

class UserActivityLogInline(admin.TabularInline):
    model = UserActivityLog
    extra = 0
    readonly_fields = ('activity_type', 'ip_address', 'user_agent', 'timestamp')
    can_delete = False
    max_num = 10

class UserVerificationInline(admin.StackedInline):
    model = UserVerification
    fk_name = 'user'  # ADDED THIS LINE - specifies which foreign key to use
    extra = 0
    readonly_fields = (
    'submitted_at',
    'verified_at',
    'document_front_preview',
    'document_back_preview',
)
    fieldsets = (
        ('Document Information', {
            'fields': ('document_type', 'document_front_preview', 'document_back_preview')
        }),
        ('Verification Status', {
            'fields': ('is_approved', 'verified_at', 'verified_by', 'verification_notes')
        }),
    )
    
    def document_front_preview(self, obj):
        if obj.document_front:
            return format_html('<img src="{}" style="max-height: 200px; max-width: 200px;" />', 
                             obj.document_front.url)
        return "No document"
    document_front_preview.short_description = "Front Document Preview"
    
    def document_back_preview(self, obj):
        if obj.document_back:
            return format_html('<img src="{}" style="max-height: 200px; max-width: 200px;" />', 
                             obj.document_back.url)
        return "No document"
    document_back_preview.short_description = "Back Document Preview"

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'verification_status', 
                   'is_active', 'date_joined', 'contribution_score')
    list_filter = ('user_type', 'verification_status', 'is_active', 
                  'is_staff', 'is_superuser', 'country', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 
                    'organization', 'country', 'city')
    ordering = ('-date_joined',)
    readonly_fields = ('uuid', 'last_login', 'date_joined', 'last_activity', 
                      'login_count', 'contribution_score')
    
    fieldsets = (
        (None, {'fields': ('username', 'password', 'uuid')}),
        ('Personal Info', {
            'fields': (
                'first_name', 'last_name', 'email', 'alternate_email',
                'date_of_birth', 'phone_number', 'profile_image', 'bio'
            )
        }),
        ('Professional Information', {
            'fields': (
                'user_type', 'organization', 'job_title', 
                'expertise', 'education', 'certifications'
            ),
            'classes': ('collapse',)
        }),
        ('Location & Preferences', {
            'fields': ('country', 'city', 'timezone', 'language_preference',
                      'email_notifications', 'newsletter_subscription'),
            'classes': ('collapse',)
        }),
        ('Status & Verification', {
            'fields': ('verification_status', 'is_active', 'is_deleted', 'deleted_at')
        }),
        ('Permissions', {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined', 'last_activity'),
            'classes': ('collapse',)
        }),
        ('Social & Stats', {
            'fields': ('social_links', 'contribution_score', 'login_count'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2',
                      'user_type', 'verification_status'),
        }),
    )
    
    inlines = [UserVerificationInline, UserActivityLogInline]
    
    actions = ['verify_users', 'deactivate_users', 'export_user_data']
    
    def verify_users(self, request, queryset):
        updated = queryset.update(verification_status='verified')
        self.message_user(request, f'{updated} users verified successfully.')
    verify_users.short_description = "Mark selected users as verified"
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users deactivated.')
    deactivate_users.short_description = "Deactivate selected users"

@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'ip_address', 'timestamp')
    list_filter = ('activity_type', 'timestamp')
    search_fields = ('user__username', 'user__email', 'ip_address')
    readonly_fields = ('user', 'activity_type', 'ip_address', 'user_agent', 
                      'details', 'timestamp')
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

@admin.register(UserVerification)
class UserVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'document_type', 'is_approved', 'submitted_at', 'verified_at')
    list_filter = ('is_approved', 'document_type', 'submitted_at')
    search_fields = ('user__username', 'user__email', 'verification_notes')
    readonly_fields = ('submitted_at',)
    raw_id_fields = ('user', 'verified_by')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'document_type')
        }),
        ('Documents', {
            'fields': ('document_front', 'document_back')
        }),
        ('Verification Process', {
            'fields': ('is_approved', 'verified_by', 'verification_notes')
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'verified_at'),
            'classes': ('collapse',)
		}),
    )
