from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class User(AbstractUser):
    """Custom User model extending AbstractUser with role field"""
    
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('parent', 'Parent'),
    ]
    
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        help_text="User role in the platform"
    )
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class StudentProfile(models.Model):
    """Profile model for students with learning preferences and progress tracking"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )
    learning_preferences = models.JSONField(
        default=dict,
        help_text="JSON field storing learning preferences and settings"
    )
    current_streak = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Current consecutive days of learning activity"
    )
    total_xp = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total experience points earned"
    )
    grade_level = models.CharField(
        max_length=20,
        blank=True,
        help_text="Student's current grade level"
    )
    subjects_of_interest = models.JSONField(
        default=list,
        help_text="List of subjects the student is interested in"
    )
    leaderboard_visible = models.BooleanField(
        default=True,
        help_text="Whether this student appears on public leaderboards"
    )
    show_real_name = models.BooleanField(
        default=False,
        help_text="Whether to show real name instead of username on leaderboards"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def level(self):
        """Calculate student level based on total XP"""
        if self.total_xp < 100:
            return 1
        elif self.total_xp < 300:
            return 2
        elif self.total_xp < 600:
            return 3
        elif self.total_xp < 1000:
            return 4
        elif self.total_xp < 1500:
            return 5
        elif self.total_xp < 2100:
            return 6
        elif self.total_xp < 2800:
            return 7
        elif self.total_xp < 3600:
            return 8
        elif self.total_xp < 4500:
            return 9
        elif self.total_xp < 5500:
            return 10
        else:
            # Level 11+ requires 1000 XP per level
            return 10 + ((self.total_xp - 5500) // 1000) + 1

    def update_learning_streak(self):
        """Update the student's learning streak based on recent activity"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Check if student has completed any lessons today
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # Import here to avoid circular imports
        from learning.models import DailyLesson
        
        # Check if there's a completed lesson today
        completed_today = DailyLesson.objects.filter(
            student=self,
            lesson_date=today,
            status='completed'
        ).exists()
        
        if completed_today:
            # Check if there was activity yesterday to continue streak
            completed_yesterday = DailyLesson.objects.filter(
                student=self,
                lesson_date=yesterday,
                status='completed'
            ).exists()
            
            if completed_yesterday or self.current_streak == 0:
                self.current_streak += 1
            else:
                # Reset streak if there was a gap
                self.current_streak = 1
        else:
            # Check if streak should be reset (no activity for more than 1 day)
            last_activity = DailyLesson.objects.filter(
                student=self,
                status='completed'
            ).order_by('-lesson_date').first()
            
            if last_activity:
                days_since_activity = (today - last_activity.lesson_date).days
                if days_since_activity > 1:
                    self.current_streak = 0
    
    def generate_parent_link_code(self):
        """Generate a simple parent link code for account linking"""
        return f"PARENT_{self.id}"
    
    def __str__(self):
        return f"Student Profile: {self.user.username}"
    
    class Meta:
        verbose_name = "Student Profile"
        verbose_name_plural = "Student Profiles"


class TeacherProfile(models.Model):
    """Profile model for teachers with subject expertise and institution info"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_profile'
    )
    institution = models.CharField(
        max_length=200,
        help_text="Name of the educational institution"
    )
    subjects = models.JSONField(
        default=list,
        help_text="List of subjects the teacher specializes in"
    )
    years_of_experience = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        help_text="Years of teaching experience"
    )
    bio = models.TextField(
        blank=True,
        help_text="Teacher's professional biography"
    )
    verified = models.BooleanField(
        default=False,
        help_text="Whether the teacher's credentials have been verified"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Teacher Profile: {self.user.username} - {self.institution}"
    
    class Meta:
        verbose_name = "Teacher Profile"
        verbose_name_plural = "Teacher Profiles"


class ParentProfile(models.Model):
    """Profile model for parents with child account linking"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='parent_profile'
    )
    children = models.ManyToManyField(
        StudentProfile,
        blank=True,
        related_name='parents',
        help_text="Student profiles linked to this parent"
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="Parent's contact phone number"
    )
    notification_preferences = models.JSONField(
        default=dict,
        help_text="JSON field storing notification preferences"
    )
    screen_time_limits = models.JSONField(
        default=dict,
        help_text="JSON field storing screen time limits for children"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Parent Profile: {self.user.username}"
    
    def get_children_count(self):
        """Return the number of children linked to this parent"""
        return self.children.count()
    
    class Meta:
        verbose_name = "Parent Profile"
        verbose_name_plural = "Parent Profiles"

# Privacy and Compliance Models

class PrivacyConsent(models.Model):
    """Track user privacy consents for GDPR compliance"""
    
    CONSENT_TYPES = [
        ('data_processing', 'Data Processing'),
        ('marketing', 'Marketing Communications'),
        ('analytics', 'Analytics and Tracking'),
        ('third_party', 'Third Party Services'),
        ('cookies', 'Cookies and Tracking'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='privacy_consents')
    consent_type = models.CharField(max_length=50, choices=CONSENT_TYPES)
    granted = models.BooleanField(default=False)
    granted_at = models.DateTimeField(null=True, blank=True)
    withdrawn_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    privacy_policy_version = models.CharField(max_length=10, default='1.0')
    
    class Meta:
        unique_together = ['user', 'consent_type']
        indexes = [
            models.Index(fields=['user', 'consent_type']),
            models.Index(fields=['granted_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.consent_type} - {'Granted' if self.granted else 'Withdrawn'}"
    
    def grant_consent(self, ip_address, user_agent):
        """Grant consent with tracking information"""
        from django.utils import timezone
        self.granted = True
        self.granted_at = timezone.now()
        self.withdrawn_at = None
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.save()
    
    def withdraw_consent(self):
        """Withdraw consent"""
        from django.utils import timezone
        self.granted = False
        self.withdrawn_at = timezone.now()
        self.save()


class DataRetentionPolicy(models.Model):
    """Define data retention policies for different data types"""
    
    DATA_TYPES = [
        ('user_profile', 'User Profile Data'),
        ('learning_data', 'Learning Progress Data'),
        ('uploaded_content', 'Uploaded Content'),
        ('analytics_data', 'Analytics Data'),
        ('communication_logs', 'Communication Logs'),
        ('session_data', 'Session Data'),
    ]
    
    data_type = models.CharField(max_length=50, choices=DATA_TYPES, unique=True)
    retention_days = models.IntegerField(help_text="Number of days to retain this data type")
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.data_type} - {self.retention_days} days"
    
    @property
    def retention_period(self):
        """Get retention period as timedelta"""
        from datetime import timedelta
        return timedelta(days=self.retention_days)


class DataDeletionRequest(models.Model):
    """Track user requests for data deletion (Right to be Forgotten)"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deletion_requests')
    request_type = models.CharField(max_length=50, default='full_deletion')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_deletions')
    reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"Deletion request for {self.user.username} - {self.status}"
    
    def mark_completed(self, processed_by=None):
        """Mark the deletion request as completed"""
        from django.utils import timezone
        self.status = 'completed'
        self.processed_at = timezone.now()
        self.processed_by = processed_by
        self.save()


class DataExportRequest(models.Model):
    """Track user requests for data export (Right to Data Portability)"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('ready', 'Ready for Download'),
        ('downloaded', 'Downloaded'),
        ('expired', 'Expired'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='export_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    download_url = models.URLField(blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    download_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"Export request for {self.user.username} - {self.status}"
    
    def mark_ready(self, download_url, file_size):
        """Mark the export as ready for download"""
        from django.utils import timezone
        from datetime import timedelta
        self.status = 'ready'
        self.processed_at = timezone.now()
        self.expires_at = timezone.now() + timedelta(days=7)  # Expires in 7 days
        self.download_url = download_url
        self.file_size = file_size
        self.save()
    
    def record_download(self):
        """Record a download of the export file"""
        self.download_count += 1
        if self.download_count == 1:
            self.status = 'downloaded'
        self.save()


class AuditLog(models.Model):
    """Audit log for tracking data access and modifications"""
    
    ACTION_TYPES = [
        ('create', 'Create'),
        ('read', 'Read'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('export', 'Export'),
        ('login', 'Login'),
        ('logout', 'Logout'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['resource_type', 'timestamp']),
        ]
    
    def __str__(self):
        username = self.user.username if self.user else 'Anonymous'
        return f"{username} - {self.action} - {self.resource_type} - {self.timestamp}"


class COPPACompliance(models.Model):
    """Track COPPA compliance for users under 13"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='coppa_compliance')
    is_under_13 = models.BooleanField(default=False)
    parent_email = models.EmailField(blank=True)
    parent_consent_given = models.BooleanField(default=False)
    parent_consent_date = models.DateTimeField(null=True, blank=True)
    verification_token = models.CharField(max_length=100, blank=True)
    verification_sent_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"COPPA Compliance for {self.user.username}"
    
    def send_parent_verification(self):
        """Send parent verification email"""
        from django.utils import timezone
        # Implementation would send email to parent
        self.verification_sent_at = timezone.now()
        self.save()
    
    def verify_parent_consent(self):
        """Mark parent consent as verified"""
        from django.utils import timezone
        self.parent_consent_given = True
        self.parent_consent_date = timezone.now()
        self.save()