"""
Management command to manually verify user accounts
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Manually verify a user account'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to verify')

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
            
            if user.email_verified and user.is_active:
                self.stdout.write(
                    self.style.WARNING(f'User {username} is already verified and active')
                )
                return
            
            user.email_verified = True
            user.is_active = True
            user.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully verified user: {username}')
            )
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User {username} does not exist')
            )