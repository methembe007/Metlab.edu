"""
Management command to initialize gamification system for existing students
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import StudentProfile
from gamification.models import VirtualCurrency, Leaderboard
from gamification.services import (
    AchievementService, LeaderboardService, 
    XPCalculationService, CoinRewardService
)


class Command(BaseCommand):
    help = 'Initialize gamification system for existing students'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset existing gamification data',
        )
    
    def handle(self, *args, **options):
        reset = options['reset']
        
        if reset:
            self.stdout.write(
                self.style.WARNING('Resetting existing gamification data...')
            )
            VirtualCurrency.objects.all().delete()
            Leaderboard.objects.all().delete()
        
        students = StudentProfile.objects.all()
        
        self.stdout.write(
            f'Initializing gamification for {students.count()} students...'
        )
        
        with transaction.atomic():
            for student in students:
                self.initialize_student_gamification(student)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully initialized gamification for {students.count()} students'
            )
        )
    
    def initialize_student_gamification(self, student_profile):
        """Initialize gamification data for a single student"""
        
        # Create virtual currency record
        currency, created = VirtualCurrency.objects.get_or_create(
            student=student_profile,
            defaults={'coins': 0}
        )
        
        if created:
            self.stdout.write(f'Created currency record for {student_profile.user.username}')
        
        # Initialize leaderboard entries
        LeaderboardService.update_student_leaderboard(student_profile)
        
        # Check for any achievements they might already qualify for
        awarded_achievements = AchievementService.check_and_award_achievements(student_profile)
        
        if awarded_achievements:
            achievement_names = [sa.achievement.name for sa in awarded_achievements]
            self.stdout.write(
                f'Awarded achievements to {student_profile.user.username}: {", ".join(achievement_names)}'
            )
        
        # Award retroactive XP for existing lessons if any
        self.award_retroactive_xp(student_profile)
    
    def award_retroactive_xp(self, student_profile):
        """Award retroactive XP for existing completed lessons"""
        try:
            from learning.models import DailyLesson
            
            completed_lessons = DailyLesson.objects.filter(
                student=student_profile,
                status='completed'
            )
            
            if completed_lessons.exists():
                # Award base XP for each completed lesson
                total_retroactive_xp = 0
                for lesson in completed_lessons:
                    # Award base lesson XP without streak bonuses for retroactive awards
                    xp_awarded = XPCalculationService._award_xp(
                        student_profile,
                        'lesson_complete',
                        10,  # Base lesson XP
                        1.0,  # No multiplier for retroactive
                        0,    # No streak bonus for retroactive
                        f"Retroactive XP for lesson on {lesson.lesson_date}"
                    )
                    total_retroactive_xp += xp_awarded
                
                if total_retroactive_xp > 0:
                    self.stdout.write(
                        f'Awarded {total_retroactive_xp} retroactive XP to {student_profile.user.username}'
                    )
        
        except ImportError:
            # learning models not available yet
            pass