"""
Management command to generate daily lessons for all students
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import StudentProfile
from learning.services import DailyLessonService


class Command(BaseCommand):
    help = 'Generate daily lessons for all students'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date to generate lessons for (YYYY-MM-DD format). Defaults to today.'
        )
        parser.add_argument(
            '--student-id',
            type=int,
            help='Generate lesson for specific student ID only'
        )
        parser.add_argument(
            '--days-ahead',
            type=int,
            default=1,
            help='Number of days ahead to generate lessons for (default: 1)'
        )
    
    def handle(self, *args, **options):
        # Parse date
        if options['date']:
            try:
                from datetime import datetime
                lesson_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Invalid date format. Use YYYY-MM-DD')
                )
                return
        else:
            lesson_date = timezone.now().date()
        
        # Get students to generate lessons for
        if options['student_id']:
            try:
                students = [StudentProfile.objects.get(id=options['student_id'])]
            except StudentProfile.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Student with ID {options["student_id"]} not found')
                )
                return
        else:
            students = StudentProfile.objects.all()
        
        days_ahead = options['days_ahead']
        total_generated = 0
        total_students = len(students)
        
        self.stdout.write(
            f'Generating lessons for {total_students} students, '
            f'{days_ahead} days ahead starting from {lesson_date}'
        )
        
        for student in students:
            student_lessons_generated = 0
            
            for day_offset in range(days_ahead):
                current_date = lesson_date + timezone.timedelta(days=day_offset)
                
                try:
                    lesson = DailyLessonService.generate_daily_lesson(student, current_date)
                    if lesson:
                        student_lessons_generated += 1
                        total_generated += 1
                        
                        self.stdout.write(
                            f'Generated lesson for {student.user.username} on {current_date}: '
                            f'"{lesson.title}" ({lesson.lesson_type})'
                        )
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Error generating lesson for {student.user.username} '
                            f'on {current_date}: {str(e)}'
                        )
                    )
            
            if student_lessons_generated > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Generated {student_lessons_generated} lessons for {student.user.username}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully generated {total_generated} lessons total'
            )
        )
        
        # Show summary statistics
        self.show_lesson_statistics()
    
    def show_lesson_statistics(self):
        """Show statistics about generated lessons"""
        from learning.models import DailyLesson
        from collections import Counter
        
        today = timezone.now().date()
        
        # Get lessons for today
        today_lessons = DailyLesson.objects.filter(lesson_date=today)
        
        if today_lessons.exists():
            lesson_types = Counter(today_lessons.values_list('lesson_type', flat=True))
            
            self.stdout.write('\n--- Today\'s Lesson Statistics ---')
            self.stdout.write(f'Total lessons scheduled: {today_lessons.count()}')
            
            for lesson_type, count in lesson_types.items():
                self.stdout.write(f'{lesson_type.replace("_", " ").title()}: {count}')
            
            # Show difficulty distribution
            difficulty_levels = Counter(today_lessons.values_list('difficulty_level', flat=True))
            self.stdout.write('\nDifficulty Distribution:')
            for difficulty, count in difficulty_levels.items():
                self.stdout.write(f'{difficulty.title()}: {count}')