from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from accounts.models import TeacherProfile, StudentProfile
from content.models import UploadedContent, GeneratedQuiz
import string
import random

User = get_user_model()


class TeacherClass(models.Model):
    """Model for teacher-created classes"""
    
    teacher = models.ForeignKey(
        TeacherProfile,
        on_delete=models.CASCADE,
        related_name='classes',
        help_text="Teacher who created this class"
    )
    name = models.CharField(
        max_length=200,
        help_text="Name of the class"
    )
    subject = models.CharField(
        max_length=100,
        help_text="Subject taught in this class"
    )
    grade_level = models.CharField(
        max_length=20,
        help_text="Grade level for this class"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of the class"
    )
    invitation_code = models.CharField(
        max_length=8,
        unique=True,
        help_text="Unique code for students to join the class"
    )
    max_students = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Maximum number of students allowed in this class"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the class is currently active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.invitation_code:
            self.invitation_code = self.generate_invitation_code()
        super().save(*args, **kwargs)
    
    def generate_invitation_code(self):
        """Generate a unique 8-character invitation code"""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not TeacherClass.objects.filter(invitation_code=code).exists():
                return code
    
    def get_student_count(self):
        """Get the number of enrolled students"""
        return self.enrollments.filter(is_active=True).count()
    
    def can_enroll_students(self):
        """Check if more students can be enrolled"""
        return self.get_student_count() < self.max_students
    
    def __str__(self):
        return f"{self.name} - {self.teacher.user.username}"
    
    class Meta:
        verbose_name = "Teacher Class"
        verbose_name_plural = "Teacher Classes"
        ordering = ['-created_at']


class ClassEnrollment(models.Model):
    """Model for student enrollment in teacher classes"""
    
    teacher_class = models.ForeignKey(
        TeacherClass,
        on_delete=models.CASCADE,
        related_name='enrollments',
        help_text="Class the student is enrolled in"
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='class_enrollments',
        help_text="Student enrolled in the class"
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the enrollment is currently active"
    )
    
    def __str__(self):
        return f"{self.student.user.username} in {self.teacher_class.name}"
    
    class Meta:
        verbose_name = "Class Enrollment"
        verbose_name_plural = "Class Enrollments"
        unique_together = ['teacher_class', 'student']
        ordering = ['-enrolled_at']


class TeacherContent(models.Model):
    """Model for content uploaded by teachers for their classes"""
    
    teacher = models.ForeignKey(
        TeacherProfile,
        on_delete=models.CASCADE,
        related_name='teacher_content',
        help_text="Teacher who uploaded this content"
    )
    uploaded_content = models.OneToOneField(
        UploadedContent,
        on_delete=models.CASCADE,
        related_name='teacher_content',
        help_text="The uploaded content file"
    )
    assigned_classes = models.ManyToManyField(
        TeacherClass,
        blank=True,
        related_name='assigned_content',
        help_text="Classes this content is assigned to"
    )
    title = models.CharField(
        max_length=200,
        help_text="Title for the content"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of the content"
    )
    subject = models.CharField(
        max_length=100,
        help_text="Subject this content covers"
    )
    grade_level = models.CharField(
        max_length=20,
        help_text="Appropriate grade level for this content"
    )
    is_public = models.BooleanField(
        default=False,
        help_text="Whether this content is available to all students"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.teacher.user.username}"
    
    class Meta:
        verbose_name = "Teacher Content"
        verbose_name_plural = "Teacher Content"
        ordering = ['-created_at']


class TeacherQuiz(models.Model):
    """Model for quizzes created/customized by teachers"""
    
    teacher = models.ForeignKey(
        TeacherProfile,
        on_delete=models.CASCADE,
        related_name='teacher_quizzes',
        help_text="Teacher who created/customized this quiz"
    )
    generated_quiz = models.ForeignKey(
        GeneratedQuiz,
        on_delete=models.CASCADE,
        related_name='teacher_customizations',
        help_text="The AI-generated quiz this is based on"
    )
    customized_questions = models.JSONField(
        help_text="Customized quiz questions with teacher modifications"
    )
    assigned_classes = models.ManyToManyField(
        TeacherClass,
        blank=True,
        related_name='assigned_quizzes',
        help_text="Classes this quiz is assigned to"
    )
    title = models.CharField(
        max_length=200,
        help_text="Custom title for the quiz"
    )
    instructions = models.TextField(
        blank=True,
        help_text="Special instructions for students"
    )
    time_limit_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(5), MaxValueValidator(180)],
        help_text="Time limit for the quiz in minutes"
    )
    attempts_allowed = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Number of attempts allowed per student"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the quiz is currently available to students"
    )
    due_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Due date for quiz completion"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_question_count(self):
        """Get the number of questions in the customized quiz"""
        return len(self.customized_questions)
    
    def is_overdue(self):
        """Check if the quiz is past its due date"""
        if self.due_date:
            return timezone.now() > self.due_date
        return False
    
    def __str__(self):
        return f"{self.title} - {self.teacher.user.username}"
    
    class Meta:
        verbose_name = "Teacher Quiz"
        verbose_name_plural = "Teacher Quizzes"
        ordering = ['-created_at']


class QuizAttempt(models.Model):
    """Model for tracking student attempts on teacher quizzes"""
    
    quiz = models.ForeignKey(
        TeacherQuiz,
        on_delete=models.CASCADE,
        related_name='attempts',
        help_text="Quiz this attempt is for"
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='quiz_attempts',
        help_text="Student who made this attempt"
    )
    attempt_number = models.PositiveIntegerField(
        help_text="Which attempt this is for the student"
    )
    answers = models.JSONField(
        help_text="Student's answers to the quiz questions"
    )
    score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Score achieved on this attempt (0-100)"
    )
    time_taken_minutes = models.PositiveIntegerField(
        help_text="Time taken to complete the quiz in minutes"
    )
    started_at = models.DateTimeField(
        help_text="When the student started this attempt"
    )
    completed_at = models.DateTimeField(
        help_text="When the student completed this attempt"
    )
    
    def __str__(self):
        return f"{self.student.user.username} - {self.quiz.title} (Attempt {self.attempt_number})"
    
    class Meta:
        verbose_name = "Quiz Attempt"
        verbose_name_plural = "Quiz Attempts"
        unique_together = ['quiz', 'student', 'attempt_number']
        ordering = ['-completed_at']