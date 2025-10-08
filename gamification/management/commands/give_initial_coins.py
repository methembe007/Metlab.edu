"""
Management command to give initial coins to all students for testing the shop
"""

from django.core.management.base import BaseCommand
from accounts.models import StudentProfile
from gamification.services import CoinRewardService


class Command(BaseCommand):
    help = 'Give initial coins to all students for testing the shop'

    def add_arguments(self, parser):
        parser.add_argument(
            '--amount',
            type=int,
            default=100,
            help='Amount of coins to give to each student (default: 100)'
        )
        parser.add_argument(
            '--reason',
            type=str,
            default='Initial shop testing coins',
            help='Reason for giving coins'
        )

    def handle(self, *args, **options):
        amount = options['amount']
        reason = options['reason']
        
        students = StudentProfile.objects.all()
        
        if not students.exists():
            self.stdout.write(
                self.style.WARNING('No students found in the database.')
            )
            return
        
        self.stdout.write(f'Giving {amount} coins to {students.count()} students...')
        
        for student in students:
            currency = CoinRewardService.get_or_create_currency(student)
            currency.add_coins(amount, reason)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Gave {amount} coins to {student.user.username} '
                    f'(new balance: {currency.coins})'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully gave {amount} coins to all {students.count()} students!'
            )
        )