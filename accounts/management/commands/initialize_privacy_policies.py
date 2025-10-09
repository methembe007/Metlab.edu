"""
Management command to initialize default data retention policies
"""

from django.core.management.base import BaseCommand
from accounts.models import DataRetentionPolicy


class Command(BaseCommand):
    help = 'Initialize default data retention policies'

    def handle(self, *args, **options):
        policies = [
            {
                'data_type': 'user_profile',
                'retention_days': 730,  # 2 years
                'description': 'User profile data including personal information and preferences'
            },
            {
                'data_type': 'learning_data',
                'retention_days': 1095,  # 3 years
                'description': 'Learning progress, session data, and performance analytics'
            },
            {
                'data_type': 'uploaded_content',
                'retention_days': 365,  # 1 year
                'description': 'User-uploaded files and generated content'
            },
            {
                'data_type': 'analytics_data',
                'retention_days': 180,  # 6 months
                'description': 'Usage analytics and behavioral data'
            },
            {
                'data_type': 'communication_logs',
                'retention_days': 90,  # 3 months
                'description': 'Chat logs, messages, and communication history'
            },
            {
                'data_type': 'session_data',
                'retention_days': 30,  # 1 month
                'description': 'Session data and temporary authentication tokens'
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for policy_data in policies:
            policy, created = DataRetentionPolicy.objects.get_or_create(
                data_type=policy_data['data_type'],
                defaults={
                    'retention_days': policy_data['retention_days'],
                    'description': policy_data['description'],
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created retention policy for {policy_data['data_type']}"
                    )
                )
            else:
                # Update description if it has changed
                if policy.description != policy_data['description']:
                    policy.description = policy_data['description']
                    policy.save()
                    updated_count += 1
                    self.stdout.write(
                        f"Updated retention policy for {policy_data['data_type']}"
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Initialized {created_count} new policies, updated {updated_count} existing policies"
            )
        )