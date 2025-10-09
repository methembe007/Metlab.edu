from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, StudentProfile, TeacherProfile, ParentProfile,
    PrivacyConsent, DataRetentionPolicy, DataDeletionRequest, 
    DataExportRequest, AuditLog, COPPACompliance
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin with role field"""
    
    list_display = ('username', 'email', 'role', 'email_verified', 'is_active', 'date_joined')
    list_filter = ('role', 'email_verified', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'email_verified')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'email')
        }),
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    """Admin interface for Student profiles"""
    
    list_display = ('user', 'current_streak', 'total_xp', 'grade_level', 'created_at')
    list_filter = ('grade_level', 'created_at')
    search_fields = ('user__username', 'user__email', 'grade_level')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Learning Progress', {
            'fields': ('current_streak', 'total_xp', 'grade_level')
        }),
        ('Preferences', {
            'fields': ('learning_preferences', 'subjects_of_interest')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    """Admin interface for Teacher profiles"""
    
    list_display = ('user', 'institution', 'years_of_experience', 'verified', 'created_at')
    list_filter = ('verified', 'years_of_experience', 'created_at')
    search_fields = ('user__username', 'user__email', 'institution')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Professional Information', {
            'fields': ('institution', 'subjects', 'years_of_experience', 'bio', 'verified')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    """Admin interface for Parent profiles"""
    
    list_display = ('user', 'get_children_count', 'phone_number', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('children',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Contact Information', {
            'fields': ('phone_number',)
        }),
        ('Children', {
            'fields': ('children',)
        }),
        ('Settings', {
            'fields': ('notification_preferences', 'screen_time_limits')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

# Privacy and Compliance Admin

@admin.register(PrivacyConsent)
class PrivacyConsentAdmin(admin.ModelAdmin):
    """Admin interface for Privacy Consents"""
    
    list_display = ('user', 'consent_type', 'granted', 'granted_at', 'privacy_policy_version')
    list_filter = ('consent_type', 'granted', 'granted_at', 'privacy_policy_version')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('granted_at', 'withdrawn_at', 'ip_address', 'user_agent')
    
    fieldsets = (
        ('Consent Information', {
            'fields': ('user', 'consent_type', 'granted', 'privacy_policy_version')
        }),
        ('Tracking Information', {
            'fields': ('granted_at', 'withdrawn_at', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DataRetentionPolicy)
class DataRetentionPolicyAdmin(admin.ModelAdmin):
    """Admin interface for Data Retention Policies"""
    
    list_display = ('data_type', 'retention_days', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('data_type', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Policy Information', {
            'fields': ('data_type', 'retention_days', 'description', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DataDeletionRequest)
class DataDeletionRequestAdmin(admin.ModelAdmin):
    """Admin interface for Data Deletion Requests"""
    
    list_display = ('user', 'status', 'requested_at', 'processed_at', 'processed_by')
    list_filter = ('status', 'requested_at', 'processed_at')
    search_fields = ('user__username', 'user__email', 'reason')
    readonly_fields = ('requested_at',)
    
    fieldsets = (
        ('Request Information', {
            'fields': ('user', 'request_type', 'status', 'reason')
        }),
        ('Processing Information', {
            'fields': ('processed_at', 'processed_by', 'notes')
        }),
        ('Timestamps', {
            'fields': ('requested_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_completed', 'mark_processing']
    
    def mark_completed(self, request, queryset):
        """Mark selected requests as completed"""
        updated = queryset.update(status='completed', processed_by=request.user)
        self.message_user(request, f'{updated} requests marked as completed.')
    mark_completed.short_description = "Mark selected requests as completed"
    
    def mark_processing(self, request, queryset):
        """Mark selected requests as processing"""
        updated = queryset.update(status='processing', processed_by=request.user)
        self.message_user(request, f'{updated} requests marked as processing.')
    mark_processing.short_description = "Mark selected requests as processing"


@admin.register(DataExportRequest)
class DataExportRequestAdmin(admin.ModelAdmin):
    """Admin interface for Data Export Requests"""
    
    list_display = ('user', 'status', 'requested_at', 'processed_at', 'expires_at', 'download_count')
    list_filter = ('status', 'requested_at', 'processed_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('requested_at', 'download_count')
    
    fieldsets = (
        ('Request Information', {
            'fields': ('user', 'status', 'requested_at')
        }),
        ('Export Information', {
            'fields': ('processed_at', 'expires_at', 'download_url', 'file_size', 'download_count')
        }),
    )
    
    actions = ['mark_ready', 'mark_processing']
    
    def mark_ready(self, request, queryset):
        """Mark selected requests as ready"""
        updated = queryset.update(status='ready')
        self.message_user(request, f'{updated} requests marked as ready.')
    mark_ready.short_description = "Mark selected requests as ready"
    
    def mark_processing(self, request, queryset):
        """Mark selected requests as processing"""
        updated = queryset.update(status='processing')
        self.message_user(request, f'{updated} requests marked as processing.')
    mark_processing.short_description = "Mark selected requests as processing"


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for Audit Logs"""
    
    list_display = ('user', 'action', 'resource_type', 'resource_id', 'timestamp', 'ip_address')
    list_filter = ('action', 'resource_type', 'timestamp')
    search_fields = ('user__username', 'resource_type', 'resource_id', 'ip_address')
    readonly_fields = ('timestamp',)
    
    fieldsets = (
        ('Log Information', {
            'fields': ('user', 'action', 'resource_type', 'resource_id', 'timestamp')
        }),
        ('Request Information', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Details', {
            'fields': ('details',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Disable adding audit logs through admin"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable changing audit logs through admin"""
        return False


@admin.register(COPPACompliance)
class COPPAComplianceAdmin(admin.ModelAdmin):
    """Admin interface for COPPA Compliance"""
    
    list_display = ('user', 'is_under_13', 'parent_consent_given', 'parent_consent_date')
    list_filter = ('is_under_13', 'parent_consent_given', 'parent_consent_date')
    search_fields = ('user__username', 'user__email', 'parent_email')
    readonly_fields = ('verification_sent_at', 'parent_consent_date')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'is_under_13')
        }),
        ('Parent Information', {
            'fields': ('parent_email', 'parent_consent_given', 'parent_consent_date')
        }),
        ('Verification', {
            'fields': ('verification_token', 'verification_sent_at'),
            'classes': ('collapse',)
        }),
    )


