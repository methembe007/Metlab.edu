"""
Management command to clean up old data based on retention policies
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import logging

from accounts.models import DataRetentionPolicy, AuditLog
from content.models import UploadedContent
from learning.models import LearningSession

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up old data based on retention policies'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--data-type',
            type=str,
            help='Clean up specific data type only',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        specific_data_type = options['data_type']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No data will be deleted')
            )
        
        # Get active retention policies
        policies = DataRetentionPolicy.objects.filter(is_active=True)
        
        if specific_data_type:
            policies = policies.filter(data_type=specific_data_type)
        
        total_deleted = 0
        
        for policy in policies:
            deleted_count = self.cleanup_data_type(policy, dry_run)
            total_deleted += deleted_count
            
            self.stdout.write(
                f"Processed {policy.data_type}: {deleted_count} records"
            )
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY RUN: Would delete {total_deleted} total records'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {total_deleted} total records'
                )
            )

    def cleanup_data_type(self, policy, dry_run=False):
        """Clean up data for a specific data type"""
        cutoff_date = timezone.now() - policy.retention_period
        deleted_count = 0
        
        try:
            if policy.data_type == 'user_profile':
                # Don't delete active user profiles, only inactive ones
                # This would need more complex logic in a real implementation
                pass
                
            elif policy.data_type == 'learning_data':
                queryset = LearningSession.objects.filter(
                    start_time__lt=cutoff_date
                )
                deleted_count = queryset.count()
                if not dry_run:
                    queryset.delete()
                    
            elif policy.data_type == 'uploaded_content':
                queryset = UploadedContent.objects.filter(
                    uploaded_at__lt=cutoff_date
                )
                deleted_count = queryset.count()
                if not dry_run:
                    # Delete associated files first
                    for content in queryset:
                        if content.file:
                            try:
                                content.file.delete(save=False)
                            except Exception as e:
                                logger.error(f"Error deleting file: {e}")
                    queryset.delete()
                    
            elif policy.data_type == 'analytics_data':
                # Clean up analytics data (would need specific models)
                pass
                
            elif policy.data_type == 'communication_logs':
                # Clean up communication logs (would need specific models)
                pass
                
            elif policy.data_type == 'session_data':
                # Django sessions are handled by Django's clearsessions command
                pass
                
            else:
                logger.warning(f"Unknown data type: {policy.data_type}")
                
        except Exception as e:
            logger.error(f"Error cleaning up {policy.data_type}: {e}")
            self.stdout.write(
                self.style.ERROR(
                    f"Error cleaning up {policy.data_type}: {e}"
                )
            )
        
        return deleted_count

    def cleanup_audit_logs(self, retention_days=90, dry_run=False):
        """Clean up old audit logs"""
        cutoff_date = timezone.now() - timedelta(days=retention_days)
        
        queryset = AuditLog.objects.filter(timestamp__lt=cutoff_date)
        deleted_count = queryset.count()
        
        if not dry_run:
            queryset.delete()
        
        return deleted_count