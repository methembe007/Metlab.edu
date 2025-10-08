import os
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

User = get_user_model()


def validate_file_size(value):
    """Validate that uploaded file is not larger than 50MB"""
    filesize = value.size
    if filesize > 50 * 1024 * 1024:  # 50MB
        raise ValidationError("File size cannot exceed 50MB")


def content_upload_path(instance, filename):
    """Generate upload path for content files"""
    # Create path: uploads/user_id/year/month/filename
    return f'uploads/{instance.user.id}/{timezone.now().year}/{timezone.now().month}/{filename}'


class UploadedContent(models.Model):
    """Model for storing uploaded content files with metadata"""
    
    CONTENT_TYPE_CHOICES = [
        ('pdf', 'PDF Document'),
        ('docx', 'Word Document'),
        ('txt', 'Text File'),
        ('image', 'Image File'),
        ('pptx', 'PowerPoint Presentation'),
    ]
    
    PROCESSING_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploaded_content',
        help_text="User who uploaded the content"
    )
    file = models.FileField(
        upload_to=content_upload_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'pptx']
            ),
            validate_file_size
        ],
        help_text="Uploaded content file"
    )
    original_filename = models.CharField(
        max_length=255,
        help_text="Original name of the uploaded file"
    )
    content_type = models.CharField(
        max_length=10,
        choices=CONTENT_TYPE_CHOICES,
        help_text="Type of content uploaded"
    )
    file_size = models.PositiveIntegerField(
        help_text="File size in bytes"
    )
    processing_status = models.CharField(
        max_length=15,
        choices=PROCESSING_STATUS_CHOICES,
        default='pending',
        help_text="Current processing status"
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when processing was completed"
    )
    key_concepts = models.JSONField(
        null=True,
        blank=True,
        help_text="AI-extracted key concepts from the content"
    )
    extracted_text = models.TextField(
        blank=True,
        help_text="Extracted text content from the file"
    )
    subject = models.CharField(
        max_length=100,
        blank=True,
        help_text="Subject/topic of the content"
    )
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        default='intermediate',
        help_text="Difficulty level of the content"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if self.file:
            self.original_filename = self.file.name
            self.file_size = self.file.size
            # Determine content type from file extension
            ext = os.path.splitext(self.file.name)[1].lower()
            if ext == '.pdf':
                self.content_type = 'pdf'
            elif ext == '.docx':
                self.content_type = 'docx'
            elif ext == '.txt':
                self.content_type = 'txt'
            elif ext in ['.jpg', '.jpeg', '.png']:
                self.content_type = 'image'
            elif ext == '.pptx':
                self.content_type = 'pptx'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.original_filename} - {self.user.username}"
    
    class Meta:
        verbose_name = "Uploaded Content"
        verbose_name_plural = "Uploaded Content"
        ordering = ['-created_at']


class GeneratedSummary(models.Model):
    """Model for AI-generated summaries of uploaded content"""
    
    SUMMARY_TYPE_CHOICES = [
        ('short', 'Short Summary'),
        ('medium', 'Medium Summary'),
        ('detailed', 'Detailed Summary'),
    ]
    
    content = models.ForeignKey(
        UploadedContent,
        on_delete=models.CASCADE,
        related_name='summaries',
        help_text="Content this summary was generated from"
    )
    summary_type = models.CharField(
        max_length=10,
        choices=SUMMARY_TYPE_CHOICES,
        help_text="Type/length of the summary"
    )
    text = models.TextField(
        help_text="Generated summary text"
    )
    word_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of words in the summary"
    )
    key_points = models.JSONField(
        default=list,
        help_text="List of key points covered in the summary"
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if self.text:
            self.word_count = len(self.text.split())
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.get_summary_type_display()} - {self.content.original_filename}"
    
    class Meta:
        verbose_name = "Generated Summary"
        verbose_name_plural = "Generated Summaries"
        unique_together = ['content', 'summary_type']


class GeneratedQuiz(models.Model):
    """Model for AI-generated quizzes from uploaded content"""
    
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    content = models.ForeignKey(
        UploadedContent,
        on_delete=models.CASCADE,
        related_name='quizzes',
        help_text="Content this quiz was generated from"
    )
    title = models.CharField(
        max_length=200,
        help_text="Title of the quiz"
    )
    questions = models.JSONField(
        help_text="JSON array of quiz questions with answers and options"
    )
    difficulty_level = models.CharField(
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default='medium',
        help_text="Difficulty level of the quiz"
    )
    question_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of questions in the quiz"
    )
    estimated_time_minutes = models.PositiveIntegerField(
        default=10,
        validators=[MaxValueValidator(120)],
        help_text="Estimated time to complete the quiz in minutes"
    )
    topics_covered = models.JSONField(
        default=list,
        help_text="List of topics/concepts covered in the quiz"
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if self.questions:
            self.question_count = len(self.questions)
            # Estimate time: 1 minute per question + 2 minutes base time
            self.estimated_time_minutes = max(5, self.question_count + 2)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Quiz: {self.title} ({self.question_count} questions)"
    
    class Meta:
        verbose_name = "Generated Quiz"
        verbose_name_plural = "Generated Quizzes"


class Flashcard(models.Model):
    """Model for AI-generated flashcards from uploaded content"""
    
    content = models.ForeignKey(
        UploadedContent,
        on_delete=models.CASCADE,
        related_name='flashcards',
        help_text="Content this flashcard was generated from"
    )
    front_text = models.TextField(
        help_text="Text displayed on the front of the flashcard (question/term)"
    )
    back_text = models.TextField(
        help_text="Text displayed on the back of the flashcard (answer/definition)"
    )
    concept_tag = models.CharField(
        max_length=100,
        help_text="Tag identifying the concept this flashcard covers"
    )
    difficulty_level = models.CharField(
        max_length=10,
        choices=[
            ('easy', 'Easy'),
            ('medium', 'Medium'),
            ('hard', 'Hard'),
        ],
        default='medium',
        help_text="Difficulty level of the flashcard"
    )
    order_index = models.PositiveIntegerField(
        default=0,
        help_text="Order of this flashcard within the content set"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Flashcard: {self.concept_tag} - {self.front_text[:50]}..."
    
    class Meta:
        verbose_name = "Flashcard"
        verbose_name_plural = "Flashcards"
        ordering = ['content', 'order_index']
