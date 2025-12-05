from django.contrib import admin
from .models import VideoSession, VideoSessionParticipant, VideoSessionEvent, VideoSessionReport


@admin.register(VideoSession)
class VideoSessionAdmin(admin.ModelAdmin):
    list_display = ['title', 'session_type', 'host', 'status', 'scheduled_time', 'started_at', 'ended_at']
    list_filter = ['session_type', 'status', 'is_recorded', 'created_at']
    search_fields = ['title', 'host__username', 'description']
    readonly_fields = ['session_id', 'created_at', 'updated_at']
    date_hierarchy = 'scheduled_time'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('session_id', 'title', 'description', 'session_type', 'host', 'status')
        }),
        ('Scheduling', {
            'fields': ('scheduled_time', 'duration_minutes', 'started_at', 'ended_at')
        }),
        ('Relationships', {
            'fields': ('teacher_class', 'tutor_booking')
        }),
        ('Recording', {
            'fields': ('is_recorded', 'recording_url', 'recording_size_bytes')
        }),
        ('Settings', {
            'fields': ('max_participants', 'allow_screen_share', 'require_approval')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(VideoSessionParticipant)
class VideoSessionParticipantAdmin(admin.ModelAdmin):
    list_display = ['user', 'session', 'role', 'status', 'joined_at', 'left_at', 'audio_enabled', 'video_enabled']
    list_filter = ['role', 'status', 'audio_enabled', 'video_enabled', 'screen_sharing']
    search_fields = ['user__username', 'session__title']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Participant Information', {
            'fields': ('session', 'user', 'role', 'status')
        }),
        ('Session Times', {
            'fields': ('joined_at', 'left_at')
        }),
        ('Media State', {
            'fields': ('audio_enabled', 'video_enabled', 'screen_sharing', 'connection_quality')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(VideoSessionEvent)
class VideoSessionEventAdmin(admin.ModelAdmin):
    list_display = ['session', 'event_type', 'user', 'timestamp']
    list_filter = ['event_type', 'timestamp']
    search_fields = ['session__title', 'user__username']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Event Information', {
            'fields': ('session', 'event_type', 'user', 'details', 'timestamp')
        }),
    )


@admin.register(VideoSessionReport)
class VideoSessionReportAdmin(admin.ModelAdmin):
    list_display = ['session', 'reporter', 'reported_user', 'report_type', 'severity', 'status', 'created_at']
    list_filter = ['report_type', 'status', 'severity', 'created_at']
    search_fields = ['session__title', 'reporter__username', 'reported_user__username', 'description']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Report Information', {
            'fields': ('session', 'reporter', 'reported_user', 'report_type', 'severity', 'status')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Review', {
            'fields': ('reviewed_by', 'reviewed_at', 'moderator_notes', 'action_taken', 'resolved_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_investigating', 'mark_as_resolved', 'mark_as_dismissed']
    
    def mark_as_investigating(self, request, queryset):
        """Mark selected reports as under investigation"""
        count = 0
        for report in queryset:
            if report.status == 'pending':
                report.mark_investigating(request.user)
                count += 1
        self.message_user(request, f"{count} report(s) marked as investigating.")
    mark_as_investigating.short_description = "Mark as investigating"
    
    def mark_as_resolved(self, request, queryset):
        """Mark selected reports as resolved"""
        count = 0
        for report in queryset:
            if report.status in ['pending', 'investigating']:
                report.mark_resolved(request.user, "Resolved by admin action")
                count += 1
        self.message_user(request, f"{count} report(s) marked as resolved.")
    mark_as_resolved.short_description = "Mark as resolved"
    
    def mark_as_dismissed(self, request, queryset):
        """Mark selected reports as dismissed"""
        count = 0
        for report in queryset:
            if report.status in ['pending', 'investigating']:
                report.mark_dismissed(request.user, "Dismissed by admin action")
                count += 1
        self.message_user(request, f"{count} report(s) marked as dismissed.")
    mark_as_dismissed.short_description = "Mark as dismissed"
