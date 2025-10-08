from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, StudentProfile, TeacherProfile, ParentProfile


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
