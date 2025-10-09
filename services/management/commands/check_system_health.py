"""
Management command to check system health and send alerts.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import models
from datetime import timedelta
from services.monitoring import alerting, monitoring
from services.models import ErrorLog, PerformanceLog, AIProcessingMetrics, AlertLog


class Command(BaseCommand):
    help = 'Check system health and generate alerts if needed'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=1,
            help='Number of hours to check (default: 1)'
        )

    def handle(self, *args, **options):
        hours = options['hours']
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=hours)
        
        self.stdout.write(f'Checking system health for the last {hours} hour(s)...')
        
        # Check error rate
        error_count = ErrorLog.objects.filter(
            timestamp__gte=start_time,
            resolved=False
        ).count()
        
        if error_count > 10:  # Threshold
            self.create_alert(
                'high_error_rate',
                'High Error Rate Detected',
                f'Detected {error_count} unresolved errors in the last {hours} hour(s)',
                'high' if error_count > 50 else 'medium'
            )
            self.stdout.write(
                self.style.WARNING(f'High error rate: {error_count} errors')
            )
        
        # Check AI processing performance
        ai_stats = AIProcessingMetrics.objects.filter(
            timestamp__gte=start_time
        ).aggregate(
            avg_time=models.Avg('processing_time'),
            success_rate=models.Avg('success')
        )
        
        if ai_stats['avg_time'] and ai_stats['avg_time'] > 30:  # 30 seconds threshold
            self.create_alert(
                'slow_ai_processing',
                'Slow AI Processing Detected',
                f'Average AI processing time: {ai_stats["avg_time"]:.2f} seconds',
                'medium'
            )
            self.stdout.write(
                self.style.WARNING(f'Slow AI processing: {ai_stats["avg_time"]:.2f}s')
            )
        
        if ai_stats['success_rate'] and ai_stats['success_rate'] < 0.95:  # 95% threshold
            success_percentage = ai_stats['success_rate'] * 100
            self.create_alert(
                'low_ai_success_rate',
                'Low AI Processing Success Rate',
                f'AI processing success rate: {success_percentage:.1f}%',
                'high' if success_percentage < 90 else 'medium'
            )
            self.stdout.write(
                self.style.WARNING(f'Low AI success rate: {success_percentage:.1f}%')
            )
        
        # Check for slow requests
        slow_requests = PerformanceLog.objects.filter(
            timestamp__gte=start_time,
            duration__gt=10.0  # 10 seconds threshold
        ).count()
        
        if slow_requests > 5:
            self.create_alert(
                'slow_requests',
                'Multiple Slow Requests Detected',
                f'Detected {slow_requests} requests taking over 10 seconds',
                'medium'
            )
            self.stdout.write(
                self.style.WARNING(f'Slow requests: {slow_requests} requests > 10s')
            )
        
        # Check for critical errors
        critical_errors = ErrorLog.objects.filter(
            timestamp__gte=start_time,
            error_type__in=['DatabaseError', 'ConnectionError', 'TimeoutError'],
            resolved=False
        ).count()
        
        if critical_errors > 0:
            self.create_alert(
                'critical_system_errors',
                'Critical System Errors Detected',
                f'Detected {critical_errors} critical system errors',
                'critical'
            )
            self.stdout.write(
                self.style.ERROR(f'Critical errors: {critical_errors}')
            )
        
        self.stdout.write(
            self.style.SUCCESS('System health check completed')
        )
    
    def create_alert(self, alert_type, title, description, severity):
        """Create an alert if it doesn't already exist."""
        # Check if similar alert already exists in the last hour
        existing_alert = AlertLog.objects.filter(
            alert_type=alert_type,
            status__in=['open', 'acknowledged'],
            timestamp__gte=timezone.now() - timedelta(hours=1)
        ).first()
        
        if not existing_alert:
            AlertLog.objects.create(
                alert_type=alert_type,
                title=title,
                description=description,
                severity=severity,
                correlation_id=monitoring.generate_correlation_id()
            )
            self.stdout.write(f'Created alert: {title}')