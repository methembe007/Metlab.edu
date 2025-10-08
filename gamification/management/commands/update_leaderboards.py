"""
Management command to update leaderboard rankings and calculate XP for all students
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import StudentProfile
from gamification.services import LeaderboardService


class Command(BaseCommand):
    help = 'Update leaderboard rankings and XP calculations for all students'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update all leaderboard entries even if recently updated',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting leaderboard update...'))
        
        # Get all student profiles
        students = StudentProfile.objects.all()
        total_students = students.count()
        
        if total_students == 0:
            self.stdout.write(self.style.WARNING('No student profiles found.'))
            return
        
        self.stdout.write(f'Updating leaderboards for {total_students} students...')
        
        updated_count = 0
        for i, student in enumerate(students, 1):
            try:
                # Update general leaderboards
                LeaderboardService.update_student_leaderboard(student)
                
                # Update subject-specific leaderboards if student has subjects
                if hasattr(student, 'subjects_of_interest') and student.subjects_of_interest:
                    for subject in student.subjects_of_interest:
                        LeaderboardService.update_subject_leaderboard(student, subject)
                
                updated_count += 1
                
                # Progress indicator
                if i % 10 == 0 or i == total_students:
                    self.stdout.write(f'Progress: {i}/{total_students} students processed')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error updating student {student.user.username}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated leaderboards for {updated_count} students')
        )
        
        # Display some statistics
        from gamification.models import Leaderboard
        
        total_entries = Leaderboard.objects.count()
        visible_entries = Leaderboard.objects.filter(student__leaderboard_visible=True).count()
        
        self.stdout.write('\nLeaderboard Statistics:')
        self.stdout.write(f'  Total leaderboard entries: {total_entries}')
        self.stdout.write(f'  Visible entries: {visible_entries}')
        self.stdout.write(f'  Hidden entries: {total_entries - visible_entries}')
        
        # Show top 5 students for each leaderboard type
        for leaderboard_type in ['weekly', 'monthly', 'all_time']:
            top_students = LeaderboardService.get_top_students(
                leaderboard_type=leaderboard_type,
                limit=5
            )
            
            self.stdout.write(f'\nTop 5 - {leaderboard_type.title()} Leaderboard:')
            for entry in top_students:
                xp_field = f'{leaderboard_type}_xp'
                xp_value = getattr(entry, xp_field, 0)
                display_name = entry.student.user.first_name if entry.student.show_real_name and entry.student.user.first_name else entry.student.user.username
                self.stdout.write(f'  #{entry.rank}: {display_name} - {xp_value} XP')