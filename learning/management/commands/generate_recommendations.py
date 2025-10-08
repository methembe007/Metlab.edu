"""
Management command to generate personalized recommendations for all students
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from accounts.models import StudentProfile
from learning.analytics import RecommendationEngine, WeaknessIdentificationEngine
from learning.services import RecommendationService


class Command(BaseCommand):
    help = 'Generate personalized recommendations for all active students'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Only process students active in the last N days (default: 7)'
        )
        parser.add_argument(
            '--student-id',
            type=int,
            help='Process only a specific student by ID'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration even if recent recommendations exist'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        student_id = options.get('student_id')
        force = options['force']
        
        # Get students to process
        if student_id:
            students = StudentProfile.objects.filter(id=student_id)
            if not students.exists():
                self.stdout.write(
                    self.style.ERROR(f'Student with ID {student_id} not found')
                )
                return
        else:
            # Get students active in the last N days
            cutoff_date = timezone.now() - timedelta(days=days)
            students = StudentProfile.objects.filter(
                learning_sessions__start_time__gte=cutoff_date
            ).distinct()
        
        self.stdout.write(f'Processing {students.count()} students...')
        
        total_recommendations = 0
        processed_students = 0
        
        for student in students:
            try:
                # Check if student already has recent recommendations
                if not force:
                    recent_recommendations = student.recommendations.filter(
                        created_at__gte=timezone.now() - timedelta(hours=24),
                        status__in=['pending', 'viewed']
                    ).exists()
                    
                    if recent_recommendations:
                        self.stdout.write(f'Skipping {student.user.username} - has recent recommendations')
                        continue
                
                # Update weakness analysis
                WeaknessIdentificationEngine.update_weakness_analysis(student)
                
                # Generate comprehensive recommendations
                recommendations = RecommendationEngine.generate_comprehensive_recommendations(student)
                
                # Create recommendation objects
                created_count = 0
                for rec_data in recommendations[:5]:  # Limit to top 5
                    # Check for duplicates
                    existing = student.recommendations.filter(
                        recommendation_type=rec_data['type'],
                        title=rec_data['title'],
                        status__in=['pending', 'viewed', 'accepted']
                    ).exists()
                    
                    if not existing:
                        from learning.models import PersonalizedRecommendation
                        PersonalizedRecommendation.objects.create(
                            student=student,
                            recommendation_type=rec_data['type'],
                            title=rec_data['title'],
                            description=rec_data['description'],
                            content=rec_data['content'],
                            priority=rec_data['priority'],
                            estimated_time_minutes=rec_data['estimated_time']
                        )
                        created_count += 1
                
                total_recommendations += created_count
                processed_students += 1
                
                self.stdout.write(
                    f'Generated {created_count} recommendations for {student.user.username}'
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing {student.user.username}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {processed_students} students and generated {total_recommendations} recommendations'
            )
        )