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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
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
