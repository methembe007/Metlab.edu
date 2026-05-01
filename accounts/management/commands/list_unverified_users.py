"""
Management command to list inactive user accounts
Note: Email verification has been removed. This command now lists inactive users.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'List all inactive user accounts'

    def handle(self, *args, **options):
        inactive_users = User.objects.filter(
            is_active=False
        ).order_by('-date_joined')
        
        if not inactive_users.exists():
            self.stdout.write(
                self.style.SUCCESS('No inactive users found')
            )
            return
        
        self.stdout.write(
            self.style.WARNING(f'Found {inactive_users.count()} inactive users:')
        )
        
        for user in inactive_users:
            self.stdout.write(
                f'  - {user.username} ({user.email}) - {user.get_role_display()} - Joined: {user.date_joined.strftime("%Y-%m-%d %H:%M")}'
            )