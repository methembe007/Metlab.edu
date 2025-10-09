"""
Management command to clean up old log entries.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from services.models import (
    PerformanceLog, ErrorLog, UserActivityLog, 
    SystemMetrics, AlertLog, AIProcessingMetrics
)


class Command(BaseCommand):
    help = 'Clean up old log entries to manage database size'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to keep logs (default: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        cutoff_date = timezone.now() - timedelta(days=days)
        
        self.stdout.write(f'Cleaning up logs older than {days} days ({cutoff_date})...')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No data will be deleted'))
        
        # Clean up performance logs
        performance_count = PerformanceLog.objects.filter(
            timestamp__lt=cutoff_date
        ).count()
        
        if performance_count > 0:
            if not dry_run:
                PerformanceLog.objects.filter(timestamp__lt=cutoff_date).delete()
            self.stdout.write(f'Performance logs: {performance_count} entries')
        
        # Clean up resolved error logs (keep unresolved ones longer)
        resolved_errors_count = ErrorLog.objects.filter(
            timestamp__lt=cutoff_date,
            resolved=True
        ).count()
        
        if resolved_errors_count > 0:
            if not dry_run:
                ErrorLog.objects.filter(
                    timestamp__lt=cutoff_date,
                    resolved=True
                ).delete()
            self.stdout.write(f'Resolved error logs: {resolved_errors_count} entries')
        
        # Clean up user activity logs
        activity_count = UserActivityLog.objects.filter(
            timestamp__lt=cutoff_date
        ).count()
        
        if activity_count > 0:
            if not dry_run:
                UserActivityLog.objects.filter(timestamp__lt=cutoff_date).delete()
            self.stdout.write(f'User activity logs: {activity_count} entries')
        
        # Clean up system metrics
        metrics_count = SystemMetrics.objects.filter(
            timestamp__lt=cutoff_date
        ).count()
        
        if metrics_count > 0:
            if not dry_run:
                SystemMetrics.objects.filter(timestamp__lt=cutoff_date).delete()
            self.stdout.write(f'System metrics: {metrics_count} entries')
        
        # Clean up closed alerts
        closed_alerts_count = AlertLog.objects.filter(
            timestamp__lt=cutoff_date,
            status='closed'
        ).count()
        
        if closed_alerts_count > 0:
            if not dry_run:
                AlertLog.objects.filter(
                    timestamp__lt=cutoff_date,
                    status='closed'
                ).delete()
            self.stdout.write(f'Closed alerts: {closed_alerts_count} entries')
        
        # Clean up AI processing metrics
        ai_metrics_count = AIProcessingMetrics.objects.filter(
            timestamp__lt=cutoff_date
        ).count()
        
        if ai_metrics_count > 0:
            if not dry_run:
                AIProcessingMetrics.objects.filter(timestamp__lt=cutoff_date).delete()
            self.stdout.write(f'AI processing metrics: {ai_metrics_count} entries')
        
        total_cleaned = (
            performance_count + resolved_errors_count + activity_count + 
            metrics_count + closed_alerts_count + ai_metrics_count
        )
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'Would clean up {total_cleaned} total log entries')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Cleaned up {total_cleaned} total log entries')
            )