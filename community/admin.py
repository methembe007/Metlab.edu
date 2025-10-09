from django.contrib import admin
from .models import (Subject, TutorProfile, TutorAvailability, TutorBooking, TutorReview,
                     StudyPartnerRequest, StudyPartnership, StudySession, StudyGroup,
                     StudyGroupMembership, StudyGroupMessage, StudySessionAttendance)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


class TutorAvailabilityInline(admin.TabularInline):
    model = TutorAvailability
    extra = 0


@admin.register(TutorProfile)
class TutorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'experience_level', 'hourly_rate', 'rating', 'total_reviews', 'status', 'verified']
    list_filter = ['experience_level', 'status', 'verified', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'bio']
    filter_horizontal = ['subjects']
    inlines = [TutorAvailabilityInline]
    readonly_fields = ['rating', 'total_reviews', 'total_sessions', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'status', 'verified')
        }),
        ('Professional Details', {
            'fields': ('subjects', 'bio', 'experience_level', 'hourly_rate', 'languages', 'timezone')
        }),
        ('Statistics', {
            'fields': ('rating', 'total_reviews', 'total_sessions'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TutorAvailability)
class TutorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['tutor', 'get_day_of_week_display', 'start_time', 'end_time', 'is_available']
    list_filter = ['day_of_week', 'is_available', 'created_at']
    search_fields = ['tutor__user__username']
    ordering = ['tutor', 'day_of_week', 'start_time']


@admin.register(TutorBooking)
class TutorBookingAdmin(admin.ModelAdmin):
    list_display = ['tutor', 'student', 'subject', 'scheduled_time', 'duration_minutes', 'status', 'total_cost']
    list_filter = ['status', 'subject', 'scheduled_time', 'created_at']
    search_fields = ['tutor__user__username', 'student__user__username', 'subject__name']
    readonly_fields = ['total_cost', 'created_at', 'updated_at']
    ordering = ['-scheduled_time']
    
    fieldsets = (
        ('Booking Details', {
            'fields': ('tutor', 'student', 'subject', 'scheduled_time', 'duration_minutes', 'status')
        }),
        ('Notes', {
            'fields': ('notes', 'session_notes')
        }),
        ('Financial', {
            'fields': ('total_cost',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TutorReview)
class TutorReviewAdmin(admin.ModelAdmin):
    list_display = ['tutor', 'student', 'rating', 'would_recommend', 'created_at']
    list_filter = ['rating', 'would_recommend', 'created_at']
    search_fields = ['tutor__user__username', 'student__user__username', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(StudyPartnerRequest)
class StudyPartnerRequestAdmin(admin.ModelAdmin):
    list_display = ['requester', 'requested', 'subject', 'status', 'created_at']
    list_filter = ['status', 'subject', 'created_at']
    search_fields = ['requester__user__username', 'requested__user__username', 'subject__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Request Details', {
            'fields': ('requester', 'requested', 'subject', 'status')
        }),
        ('Message', {
            'fields': ('message',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StudyPartnership)
class StudyPartnershipAdmin(admin.ModelAdmin):
    list_display = ['student1', 'student2', 'subject', 'status', 'total_sessions', 'created_at']
    list_filter = ['status', 'subject', 'created_at']
    search_fields = ['student1__user__username', 'student2__user__username', 'subject__name']
    readonly_fields = ['total_sessions', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Partnership Details', {
            'fields': ('student1', 'student2', 'subject', 'status')
        }),
        ('Statistics', {
            'fields': ('total_sessions',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class StudySessionAttendanceInline(admin.TabularInline):
    model = StudySessionAttendance
    extra = 0
    readonly_fields = ['joined_at', 'left_at', 'created_at']


@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ['get_session_name', 'session_type', 'scheduled_time', 'duration_minutes', 'status', 'created_by']
    list_filter = ['session_type', 'status', 'scheduled_time', 'created_at']
    search_fields = ['title', 'topic', 'partnership__subject__name', 'study_group__name']
    readonly_fields = ['room_id', 'created_at', 'updated_at']
    ordering = ['-scheduled_time']
    inlines = [StudySessionAttendanceInline]
    
    def get_session_name(self, obj):
        if obj.session_type == 'partnership' and obj.partnership:
            return f"Partnership: {obj.partnership.subject.name}"
        elif obj.session_type == 'group' and obj.study_group:
            return f"Group: {obj.study_group.name}"
        return obj.title or "Untitled Session"
    get_session_name.short_description = 'Session'
    
    fieldsets = (
        ('Session Details', {
            'fields': ('session_type', 'partnership', 'study_group', 'title', 'scheduled_time', 
                      'duration_minutes', 'status', 'created_by')
        }),
        ('Content', {
            'fields': ('topic', 'description', 'session_summary')
        }),
        ('Technical', {
            'fields': ('room_id',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class StudyGroupMembershipInline(admin.TabularInline):
    model = StudyGroupMembership
    extra = 0
    readonly_fields = ['joined_at', 'updated_at']


@admin.register(StudyGroup)
class StudyGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'created_by', 'get_member_count', 'max_members', 'status', 'is_public']
    list_filter = ['status', 'is_public', 'requires_approval', 'subject', 'created_at']
    search_fields = ['name', 'description', 'created_by__user__username', 'subject__name']
    readonly_fields = ['total_sessions', 'created_at', 'updated_at']
    ordering = ['-created_at']
    inlines = [StudyGroupMembershipInline]
    
    def get_member_count(self, obj):
        return obj.get_member_count()
    get_member_count.short_description = 'Members'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'subject', 'created_by')
        }),
        ('Settings', {
            'fields': ('max_members', 'is_public', 'requires_approval', 'status')
        }),
        ('Statistics', {
            'fields': ('total_sessions',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StudyGroupMembership)
class StudyGroupMembershipAdmin(admin.ModelAdmin):
    list_display = ['study_group', 'student', 'role', 'status', 'joined_at']
    list_filter = ['role', 'status', 'joined_at']
    search_fields = ['study_group__name', 'student__user__username']
    readonly_fields = ['joined_at', 'updated_at']
    ordering = ['-joined_at']
    
    fieldsets = (
        ('Membership Details', {
            'fields': ('study_group', 'student', 'role', 'status')
        }),
        ('Timestamps', {
            'fields': ('joined_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StudyGroupMessage)
class StudyGroupMessageAdmin(admin.ModelAdmin):
    list_display = ['study_group', 'sender', 'message_type', 'get_content_preview', 'created_at']
    list_filter = ['message_type', 'is_edited', 'created_at']
    search_fields = ['study_group__name', 'sender__user__username', 'content']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    get_content_preview.short_description = 'Content'
    
    fieldsets = (
        ('Message Details', {
            'fields': ('study_group', 'sender', 'message_type', 'content')
        }),
        ('Attachments', {
            'fields': ('file_attachment',)
        }),
        ('Metadata', {
            'fields': ('is_edited',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StudySessionAttendance)
class StudySessionAttendanceAdmin(admin.ModelAdmin):
    list_display = ['session', 'student', 'status', 'joined_at', 'get_duration']
    list_filter = ['status', 'created_at']
    search_fields = ['session__title', 'student__user__username']
    readonly_fields = ['get_duration', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_duration(self, obj):
        duration = obj.get_duration_minutes()
        return f"{duration} minutes" if duration > 0 else "N/A"
    get_duration.short_description = 'Duration'
    
    fieldsets = (
        ('Attendance Details', {
            'fields': ('session', 'student', 'status')
        }),
        ('Timing', {
            'fields': ('joined_at', 'left_at', 'get_duration')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
