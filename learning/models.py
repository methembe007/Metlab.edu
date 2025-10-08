from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from accounts.models import StudentProfile
from content.models import UploadedContent
import json

User = get_user_model()


class LearningSession(models.Model):
    """Model for tracking individual learning sessions with performance metrics"""
    
    SESSION_TYPE_CHOICES = [
        ('quiz', 'Quiz Session'),
        ('flashcard', 'Flashcard Review'),
        ('summary', 'Summary Reading'),
        ('mixed', 'Mixed Learning'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('abandoned', 'Abandoned'),
    ]
    
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='learning_sessions',
        help_text="Student who participated in this session"
    )
    content = models.ForeignKey(
        UploadedContent,
        on_delete=models.CASCADE,
        related_name='learning_sessions',
        help_text="Content used in this learning session"
    )
    session_type = models.CharField(
        max_length=15,
        choices=SESSION_TYPE_CHOICES,
        help_text="Type of learning activity in this session"
    )
    start_time = models.DateTimeField(
        default=timezone.now,
        help_text="When the learning session started"
    )
    end_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the learning session ended"
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='active',
        help_text="Current status of the learning session"
    )
    performance_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Performance score as percentage (0-100)"
    )
    questions_attempted = models.PositiveIntegerField(
        default=0,
        help_text="Number of questions attempted in this session"
    )
    questions_correct = models.PositiveIntegerField(
        default=0,
        help_text="Number of questions answered correctly"
    )
    time_spent_minutes = models.PositiveIntegerField(
        default=0,
        help_text="Total time spent in minutes"
    )
    concepts_covered = models.JSONField(
        default=list,
        help_text="List of concepts covered in this session"
    )
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        default='intermediate',
        help_text="Difficulty level of the session content"
    )
    xp_earned = models.PositiveIntegerField(
        default=0,
        help_text="Experience points earned in this session"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def calculate_performance_score(self):
        """Calculate performance score based on correct answers"""
        if self.questions_attempted > 0:
            self.performance_score = (self.questions_correct / self.questions_attempted) * 100
        else:
            self.performance_score = 0.0
        return self.performance_score
    
    def calculate_time_spent(self):
        """Calculate time spent in minutes"""
        if self.end_time and self.start_time:
            duration = self.end_time - self.start_time
            self.time_spent_minutes = int(duration.total_seconds() / 60)
        return self.time_spent_minutes
    
    def end_session(self):
        """End the learning session and calculate final metrics"""
        self.end_time = timezone.now()
        self.status = 'completed'
        self.calculate_time_spent()
        self.calculate_performance_score()
        self.save()
    
    def __str__(self):
        return f"{self.student.user.username} - {self.session_type} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        verbose_name = "Learning Session"
        verbose_name_plural = "Learning Sessions"
        ordering = ['-start_time']


class WeaknessAnalysis(models.Model):
    """Model for tracking and analyzing student weaknesses in specific concepts"""
    
    WEAKNESS_LEVEL_CHOICES = [
        ('low', 'Low Weakness'),
        ('medium', 'Medium Weakness'),
        ('high', 'High Weakness'),
        ('critical', 'Critical Weakness'),
    ]
    
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='weakness_analyses',
        help_text="Student this weakness analysis belongs to"
    )
    subject = models.CharField(
        max_length=100,
        help_text="Subject area where weakness is identified"
    )
    concept = models.CharField(
        max_length=200,
        help_text="Specific concept where student shows weakness"
    )
    weakness_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Weakness score (0-100, higher means more weakness)"
    )
    weakness_level = models.CharField(
        max_length=15,
        choices=WEAKNESS_LEVEL_CHOICES,
        help_text="Categorized level of weakness"
    )
    total_attempts = models.PositiveIntegerField(
        default=0,
        help_text="Total number of attempts on this concept"
    )
    correct_attempts = models.PositiveIntegerField(
        default=0,
        help_text="Number of correct attempts on this concept"
    )
    last_attempt_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Score from the most recent attempt"
    )
    improvement_trend = models.CharField(
        max_length=20,
        choices=[
            ('improving', 'Improving'),
            ('stable', 'Stable'),
            ('declining', 'Declining'),
            ('unknown', 'Unknown'),
        ],
        default='unknown',
        help_text="Trend in performance over time"
    )
    priority_level = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Priority level for addressing this weakness (1-5, 5 is highest)"
    )
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def calculate_weakness_score(self):
        """Calculate weakness score based on performance data"""
        if self.total_attempts > 0:
            accuracy = (self.correct_attempts / self.total_attempts) * 100
            # Weakness score is inverse of accuracy
            self.weakness_score = 100 - accuracy
        else:
            self.weakness_score = 50.0  # Default moderate weakness for new concepts
        
        # Set weakness level based on score
        if self.weakness_score >= 80:
            self.weakness_level = 'critical'
            self.priority_level = 5
        elif self.weakness_score >= 60:
            self.weakness_level = 'high'
            self.priority_level = 4
        elif self.weakness_score >= 40:
            self.weakness_level = 'medium'
            self.priority_level = 3
        else:
            self.weakness_level = 'low'
            self.priority_level = 1 if self.weakness_score < 20 else 2
        
        return self.weakness_score
    
    def update_from_session(self, session):
        """Update weakness analysis based on a learning session"""
        if session.concept in session.concepts_covered:
            self.total_attempts += session.questions_attempted
            self.correct_attempts += session.questions_correct
            self.last_attempt_score = session.performance_score
            self.calculate_weakness_score()
            self.save()
    
    def __str__(self):
        return f"{self.student.user.username} - {self.concept} ({self.weakness_level})"
    
    class Meta:
        verbose_name = "Weakness Analysis"
        verbose_name_plural = "Weakness Analyses"
        unique_together = ['student', 'subject', 'concept']
        ordering = ['-priority_level', '-weakness_score']


class PersonalizedRecommendation(models.Model):
    """Model for AI-generated personalized learning recommendations"""
    
    RECOMMENDATION_TYPE_CHOICES = [
        ('content', 'Content Recommendation'),
        ('practice', 'Practice Recommendation'),
        ('review', 'Review Recommendation'),
        ('difficulty', 'Difficulty Adjustment'),
        ('study_plan', 'Study Plan'),
        ('break', 'Break Suggestion'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('viewed', 'Viewed'),
        ('accepted', 'Accepted'),
        ('dismissed', 'Dismissed'),
        ('completed', 'Completed'),
    ]
    
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='recommendations',
        help_text="Student this recommendation is for"
    )
    recommendation_type = models.CharField(
        max_length=20,
        choices=RECOMMENDATION_TYPE_CHOICES,
        help_text="Type of recommendation"
    )
    title = models.CharField(
        max_length=200,
        help_text="Title of the recommendation"
    )
    description = models.TextField(
        help_text="Detailed description of the recommendation"
    )
    content = models.JSONField(
        help_text="Structured data for the recommendation (content IDs, parameters, etc.)"
    )
    priority = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Priority level (1-5, 5 is highest priority)"
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the recommendation"
    )
    related_weakness = models.ForeignKey(
        WeaknessAnalysis,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='recommendations',
        help_text="Weakness analysis that triggered this recommendation"
    )
    related_content = models.ForeignKey(
        UploadedContent,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='recommendations',
        help_text="Content related to this recommendation"
    )
    estimated_time_minutes = models.PositiveIntegerField(
        default=10,
        help_text="Estimated time to complete this recommendation"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this recommendation expires"
    )
    viewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the student viewed this recommendation"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the student completed this recommendation"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def mark_viewed(self):
        """Mark recommendation as viewed"""
        if self.status == 'pending':
            self.status = 'viewed'
            self.viewed_at = timezone.now()
            self.save()
    
    def mark_accepted(self):
        """Mark recommendation as accepted"""
        self.status = 'accepted'
        self.save()
    
    def mark_completed(self):
        """Mark recommendation as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
    
    def mark_dismissed(self):
        """Mark recommendation as dismissed"""
        self.status = 'dismissed'
        self.save()
    
    def is_expired(self):
        """Check if recommendation has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def __str__(self):
        return f"{self.student.user.username} - {self.title} ({self.get_status_display()})"
    
    class Meta:
        verbose_name = "Personalized Recommendation"
        verbose_name_plural = "Personalized Recommendations"
        ordering = ['-priority', '-created_at']


class DailyLesson(models.Model):
    """Model for daily personalized lessons generated for students"""
    
    LESSON_STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
        ('expired', 'Expired'),
    ]
    
    LESSON_TYPE_CHOICES = [
        ('review', 'Review Lesson'),
        ('new_content', 'New Content'),
        ('weakness_focus', 'Weakness Focus'),
        ('mixed', 'Mixed Practice'),
        ('assessment', 'Assessment'),
    ]
    
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='daily_lessons',
        help_text="Student this lesson is assigned to"
    )
    lesson_date = models.DateField(
        help_text="Date this lesson is scheduled for"
    )
    lesson_type = models.CharField(
        max_length=20,
        choices=LESSON_TYPE_CHOICES,
        help_text="Type of lesson content"
    )
    title = models.CharField(
        max_length=200,
        help_text="Title of the daily lesson"
    )
    description = models.TextField(
        help_text="Description of what the lesson covers"
    )
    content_structure = models.JSONField(
        help_text="Structured lesson content including activities, questions, and materials"
    )
    estimated_duration_minutes = models.PositiveIntegerField(
        default=10,
        validators=[MinValueValidator(5), MaxValueValidator(15)],
        help_text="Estimated time to complete the lesson (5-15 minutes)"
    )
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        default='intermediate',
        help_text="Difficulty level adapted to student's progress"
    )
    priority_concepts = models.JSONField(
        default=list,
        help_text="List of key concepts this lesson focuses on"
    )
    related_content = models.ManyToManyField(
        UploadedContent,
        blank=True,
        related_name='daily_lessons',
        help_text="Content materials used in this lesson"
    )
    related_weaknesses = models.ManyToManyField(
        WeaknessAnalysis,
        blank=True,
        related_name='daily_lessons',
        help_text="Weaknesses this lesson addresses"
    )
    status = models.CharField(
        max_length=15,
        choices=LESSON_STATUS_CHOICES,
        default='scheduled',
        help_text="Current status of the lesson"
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the student started this lesson"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the student completed this lesson"
    )
    performance_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Student's performance score on this lesson"
    )
    time_spent_minutes = models.PositiveIntegerField(
        default=0,
        help_text="Actual time spent on the lesson"
    )
    xp_earned = models.PositiveIntegerField(
        default=0,
        help_text="Experience points earned from completing this lesson"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def start_lesson(self):
        """Mark lesson as started"""
        self.status = 'active'
        self.started_at = timezone.now()
        self.save()
    
    def complete_lesson(self, performance_score=None, xp_earned=None):
        """Mark lesson as completed with performance metrics"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        
        if performance_score is not None:
            self.performance_score = performance_score
        
        if xp_earned is not None:
            self.xp_earned = xp_earned
        
        # Calculate time spent
        if self.started_at:
            duration = self.completed_at - self.started_at
            self.time_spent_minutes = int(duration.total_seconds() / 60)
        
        self.save()
        
        # Update student's total XP and streak
        self.student.total_xp += self.xp_earned
        self.student.update_learning_streak()
        self.student.save()
    
    def skip_lesson(self):
        """Mark lesson as skipped"""
        self.status = 'skipped'
        self.save()
    
    def is_expired(self):
        """Check if lesson has expired (more than 1 day old)"""
        if self.lesson_date < timezone.now().date():
            return True
        return False
    
    def get_lesson_activities(self):
        """Get structured lesson activities from content_structure"""
        return self.content_structure.get('activities', [])
    
    def get_lesson_materials(self):
        """Get lesson materials from content_structure"""
        return self.content_structure.get('materials', [])
    
    def __str__(self):
        return f"{self.student.user.username} - {self.title} ({self.lesson_date})"
    
    class Meta:
        verbose_name = "Daily Lesson"
        verbose_name_plural = "Daily Lessons"
        unique_together = ['student', 'lesson_date']
        ordering = ['-lesson_date', '-created_at']


class LessonProgress(models.Model):
    """Model for tracking detailed progress within a daily lesson"""
    
    ACTIVITY_TYPE_CHOICES = [
        ('quiz', 'Quiz Question'),
        ('flashcard', 'Flashcard Review'),
        ('reading', 'Reading Activity'),
        ('practice', 'Practice Exercise'),
        ('reflection', 'Reflection Question'),
    ]
    
    lesson = models.ForeignKey(
        DailyLesson,
        on_delete=models.CASCADE,
        related_name='progress_entries',
        help_text="Lesson this progress entry belongs to"
    )
    activity_type = models.CharField(
        max_length=15,
        choices=ACTIVITY_TYPE_CHOICES,
        help_text="Type of activity completed"
    )
    activity_index = models.PositiveIntegerField(
        help_text="Index of the activity within the lesson"
    )
    concept = models.CharField(
        max_length=200,
        help_text="Concept covered in this activity"
    )
    question_text = models.TextField(
        blank=True,
        help_text="Text of the question or activity prompt"
    )
    student_answer = models.TextField(
        blank=True,
        help_text="Student's answer or response"
    )
    correct_answer = models.TextField(
        blank=True,
        help_text="Correct answer for the activity"
    )
    is_correct = models.BooleanField(
        null=True,
        blank=True,
        help_text="Whether the student's answer was correct"
    )
    time_spent_seconds = models.PositiveIntegerField(
        default=0,
        help_text="Time spent on this specific activity"
    )
    difficulty_rating = models.CharField(
        max_length=10,
        choices=[
            ('easy', 'Easy'),
            ('medium', 'Medium'),
            ('hard', 'Hard'),
        ],
        blank=True,
        help_text="Student's perceived difficulty of this activity"
    )
    completed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.lesson.title} - Activity {self.activity_index} ({self.concept})"
    
    class Meta:
        verbose_name = "Lesson Progress"
        verbose_name_plural = "Lesson Progress Entries"
        unique_together = ['lesson', 'activity_index']
        ordering = ['lesson', 'activity_index']
