"""
Models for monitoring and analytics data.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

User = get_user_model()


class PerformanceLog(models.Model):
    """Model to store performance metrics."""
    
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    operation = models.CharField(max_length=200, db_index=True)
    duration = models.FloatField()
    correlation_id = models.CharField(max_length=36, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    metadata = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'services_performance_log'
        indexes = [
            models.Index(fields=['timestamp', 'operation']),
            models.Index(fields=['operation', 'duration']),
        ]
    
    def __str__(self):
        return f"{self.operation} - {self.duration:.3f}s"


class ErrorLog(models.Model):
    """Model to store error information."""
    
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    error_type = models.CharField(max_length=200, db_index=True)
    error_message = models.TextField()
    correlation_id = models.CharField(max_length=36, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    stack_trace = models.TextField(blank=True)
    context = models.JSONField(default=dict)
    resolved = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'services_error_log'
        indexes = [
            models.Index(fields=['timestamp', 'error_type']),
            models.Index(fields=['resolved', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.error_type}: {self.error_message[:50]}"


class UserActivityLog(models.Model):
    """Model to store user activity data."""
    
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=100, db_index=True)
    correlation_id = models.CharField(max_length=36, db_index=True)
    session_id = models.CharField(max_length=40, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'services_user_activity_log'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['activity_type', 'timestamp']),
            models.Index(fields=['timestamp', 'user']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.activity_type}"


class SystemMetrics(models.Model):
    """Model to store system-wide metrics."""
    
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    metric_name = models.CharField(max_length=100, db_index=True)
    metric_value = models.FloatField()
    metric_unit = models.CharField(max_length=20, default='count')
    tags = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'services_system_metrics'
        indexes = [
            models.Index(fields=['metric_name', 'timestamp']),
            models.Index(fields=['timestamp', 'metric_name']),
        ]
    
    def __str__(self):
        return f"{self.metric_name}: {self.metric_value} {self.metric_unit}"


class AlertLog(models.Model):
    """Model to store alert information."""
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    alert_type = models.CharField(max_length=100, db_index=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    title = models.CharField(max_length=200)
    description = models.TextField()
    correlation_id = models.CharField(max_length=36, db_index=True)
    acknowledged_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='acknowledged_alerts'
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'services_alert_log'
        indexes = [
            models.Index(fields=['status', 'severity', 'timestamp']),
            models.Index(fields=['alert_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.alert_type} - {self.severity} - {self.status}"


class AIProcessingMetrics(models.Model):
    """Model to store AI processing specific metrics."""
    
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    operation_type = models.CharField(max_length=100, db_index=True)  # summary, quiz, flashcard
    content_type = models.CharField(max_length=50)  # pdf, text, etc.
    processing_time = models.FloatField()
    input_size = models.IntegerField()  # in bytes or characters
    output_size = models.IntegerField()  # in bytes or characters
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    correlation_id = models.CharField(max_length=36, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    api_calls_made = models.IntegerField(default=1)
    tokens_used = models.IntegerField(null=True, blank=True)
    cost_estimate = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    
    class Meta:
        db_table = 'services_ai_processing_metrics'
        indexes = [
            models.Index(fields=['operation_type', 'timestamp']),
            models.Index(fields=['success', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.operation_type} - {self.processing_time:.3f}s - {'Success' if self.success else 'Failed'}"