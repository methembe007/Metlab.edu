"""
Management command to list unverified user accounts
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'List all unverified user accounts'

    def handle(self, *args, **options):
        unverified_users = User.objects.filter(
            email_verified=False
        ).order_by('-date_joined')
        
        if not unverified_users.exists():
            self.stdout.write(
                self.style.SUCCESS('No unverified users found')
            )
            return
        
        self.stdout.write(
            self.style.WARNING(f'Found {unverified_users.count()} unverified users:')
        )
        
        for user in unverified_users:
            status = "Active" if user.is_active else "Inactive"
            self.stdout.write(
                f'  - {user.username} ({user.email}) - {user.get_role_display()} - {status} - Joined: {user.date_joined.strftime("%Y-%m-%d %H:%M")}'
            )