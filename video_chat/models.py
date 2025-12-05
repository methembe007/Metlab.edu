import uuid
from django.db import models
from django.conf import settings


class VideoSession(models.Model):
    """Model for video chat sessions"""
    
    SESSION_TYPE_CHOICES = [
        ('one_on_one', 'One-on-One'),
        ('group', 'Group Session'),
        ('class', 'Class Session'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    session_id = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    session_type = models.CharField(max_length=20, choices=SESSION_TYPE_CHOICES)
    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hosted_video_sessions')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    scheduled_time = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(default=60)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Relationships to existing models
    teacher_class = models.ForeignKey(
        'learning.TeacherClass',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='video_sessions'
    )
    tutor_booking = models.OneToOneField(
        'community.TutorBooking',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='video_session'
    )
    
    # Recording settings
    is_recorded = models.BooleanField(default=False)
    recording_url = models.URLField(blank=True)
    recording_size_bytes = models.BigIntegerField(null=True, blank=True)
    
    # Session settings
    max_participants = models.IntegerField(default=30)
    allow_screen_share = models.BooleanField(default=True)
    require_approval = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['host', 'status']),
            models.Index(fields=['scheduled_time']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_session_type_display()})"


class VideoSessionParticipant(models.Model):
    """Model for tracking participants in video sessions"""
    
    ROLE_CHOICES = [
        ('host', 'Host'),
        ('participant', 'Participant'),
    ]
    
    STATUS_CHOICES = [
        ('invited', 'Invited'),
        ('joined', 'Joined'),
        ('left', 'Left'),
        ('removed', 'Removed'),
    ]
    
    session = models.ForeignKey(
        VideoSession,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='participant')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='invited')
    
    joined_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)
    
    # Media state
    audio_enabled = models.BooleanField(default=True)
    video_enabled = models.BooleanField(default=True)
    screen_sharing = models.BooleanField(default=False)
    
    # Connection quality
    connection_quality = models.CharField(max_length=20, default='unknown')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['session', 'user']
        ordering = ['joined_at']
        indexes = [
            models.Index(fields=['session', 'status']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} in {self.session.title}"


class VideoSessionEvent(models.Model):
    """Model for logging events during video sessions"""
    
    EVENT_TYPE_CHOICES = [
        ('session_started', 'Session Started'),
        ('session_ended', 'Session Ended'),
        ('participant_joined', 'Participant Joined'),
        ('participant_left', 'Participant Left'),
        ('screen_share_started', 'Screen Share Started'),
        ('screen_share_stopped', 'Screen Share Stopped'),
        ('recording_started', 'Recording Started'),
        ('recording_stopped', 'Recording Stopped'),
        ('connection_issue', 'Connection Issue'),
    ]
    
    session = models.ForeignKey(
        VideoSession,
        on_delete=models.CASCADE,
        related_name='events'
    )
    event_type = models.CharField(max_length=30, choices=EVENT_TYPE_CHOICES)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    details = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['session', 'event_type']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.session.title}"


class VideoSessionReport(models.Model):
    """Model for reporting inappropriate behavior or issues in video sessions"""
    
    REPORT_TYPE_CHOICES = [
        ('inappropriate_behavior', 'Inappropriate Behavior'),
        ('harassment', 'Harassment'),
        ('bullying', 'Bullying'),
        ('spam', 'Spam'),
        ('technical_issue', 'Technical Issue'),
        ('privacy_violation', 'Privacy Violation'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
        ('escalated', 'Escalated'),
    ]
    
    session = models.ForeignKey(
        VideoSession,
        on_delete=models.CASCADE,
        related_name='reports',
        help_text="Video session being reported"
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='video_session_reports',
        help_text="User who submitted the report"
    )
    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='video_session_reports_against',
        help_text="User being reported (if applicable)"
    )
    report_type = models.CharField(
        max_length=25,
        choices=REPORT_TYPE_CHOICES,
        help_text="Type of issue being reported"
    )
    description = models.TextField(
        help_text="Detailed description of the issue"
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the report"
    )
    severity = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ],
        default='medium',
        help_text="Severity level of the reported issue"
    )
    moderator_notes = models.TextField(
        blank=True,
        help_text="Notes from moderator review"
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_video_reports',
        help_text="Moderator who reviewed this report"
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the report was reviewed"
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the issue was resolved"
    )
    action_taken = models.TextField(
        blank=True,
        help_text="Description of action taken to resolve the issue"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session', 'status']),
            models.Index(fields=['reporter', 'created_at']),
            models.Index(fields=['reported_user', 'status']),
            models.Index(fields=['status', 'severity']),
        ]
    
    def __str__(self):
        return f"Report: {self.get_report_type_display()} in {self.session.title} by {self.reporter.username}"
    
    def mark_investigating(self, reviewed_by):
        """Mark report as under investigation"""
        from django.utils import timezone
        self.status = 'investigating'
        self.reviewed_by = reviewed_by
        self.reviewed_at = timezone.now()
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'updated_at'])
    
    def mark_resolved(self, reviewed_by, action_taken=''):
        """Mark report as resolved"""
        from django.utils import timezone
        self.status = 'resolved'
        self.reviewed_by = reviewed_by
        self.reviewed_at = timezone.now()
        self.resolved_at = timezone.now()
        self.action_taken = action_taken
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'resolved_at', 'action_taken', 'updated_at'])
    
    def mark_dismissed(self, reviewed_by, reason=''):
        """Mark report as dismissed"""
        from django.utils import timezone
        self.status = 'dismissed'
        self.reviewed_by = reviewed_by
        self.reviewed_at = timezone.now()
        self.moderator_notes = reason
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'moderator_notes', 'updated_at'])
    
    def escalate(self, reviewed_by, reason=''):
        """Escalate report to higher authority"""
        from django.utils import timezone
        self.status = 'escalated'
        self.severity = 'critical'
        self.reviewed_by = reviewed_by
        self.reviewed_at = timezone.now()
        self.moderator_notes = f"Escalated: {reason}"
        self.save(update_fields=['status', 'severity', 'reviewed_by', 'reviewed_at', 'moderator_notes', 'updated_at'])
