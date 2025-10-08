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
