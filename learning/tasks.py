"""
Celery tasks for learning analytics and recommendation generation
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from accounts.models import StudentProfile
from .analytics import (
    PerformanceAnalyticsEngine,
    WeaknessIdentificationEngine, 
    RecommendationEngine
)
from .models import PersonalizedRecommendation


@shared_task
def update_student_analytics(student_profile_id):
    """Update analytics for a specific student"""
    try:
        student_profile = StudentProfile.objects.get(id=student_profile_id)
        
        # Update weakness analysis
        WeaknessIdentificationEngine.update_weakness_analysis(student_profile)
        
        # Generate new recommendations
        recommendations = RecommendationEngine.generate_comprehensive_recommendations(student_profile)
        
        # Create recommendation objects (limit to top 3 to avoid spam)
        created_count = 0
        for rec_data in recommendations[:3]:
            # Check for duplicates
            existing = PersonalizedRecommendation.objects.filter(
                student=student_profile,
                recommendation_type=rec_data['type'],
                title=rec_data['title'],
                status__in=['pending', 'viewed', 'accepted']
            ).exists()
            
            if not existing:
                PersonalizedRecommendation.objects.create(
                    student=student_profile,
                    recommendation_type=rec_data['type'],
                    title=rec_data['title'],
                    description=rec_data['description'],
                    content=rec_data['content'],
                    priority=rec_data['priority'],
                    estimated_time_minutes=rec_data['estimated_time']
                )
                created_count += 1
        
        return f"Updated analytics for {student_profile.user.username}, created {created_count} recommendations"
        
    except StudentProfile.DoesNotExist:
        return f"Student profile {student_profile_id} not found"
    except Exception as e:
        return f"Error updating analytics for student {student_profile_id}: {str(e)}"


@shared_task
def generate_daily_recommendations():
    """Generate daily recommendations for all active students"""
    # Get students who have been active in the last 7 days
    cutoff_date = timezone.now() - timedelta(days=7)
    active_students = StudentProfile.objects.filter(
        learning_sessions__start_time__gte=cutoff_date
    ).distinct()
    
    total_processed = 0
    total_recommendations = 0
    
    for student in active_students:
        try:
            # Check if student already has recent recommendations
            recent_recommendations = student.recommendations.filter(
                created_at__gte=timezone.now() - timedelta(hours=24),
                status__in=['pending', 'viewed']
            ).count()
            
            # Only generate new recommendations if they have fewer than 3 active ones
            if recent_recommendations < 3:
                # Trigger individual student analytics update
                try:
                    result = update_student_analytics.delay(student.id)
                    total_processed += 1
                except Exception as e:
                    # Fallback to synchronous processing
                    logger.warning(f"Celery task failed for student {student.id}, processing synchronously: {e}")
                    try:
                        update_student_analytics(student.id)
                        total_processed += 1
                    except Exception as sync_error:
                        logger.error(f"Synchronous processing failed for student {student.id}: {sync_error}")
                        continue
        
        except Exception as e:
            continue  # Skip problematic students
    
    return f"Queued analytics updates for {total_processed} students"


@shared_task
def cleanup_old_recommendations():
    """Clean up old and expired recommendations"""
    # Delete recommendations older than 30 days that are dismissed or completed
    old_date = timezone.now() - timedelta(days=30)
    deleted_count = PersonalizedRecommendation.objects.filter(
        created_at__lt=old_date,
        status__in=['dismissed', 'completed']
    ).delete()[0]
    
    # Mark expired recommendations as dismissed
    expired_count = PersonalizedRecommendation.objects.filter(
        expires_at__lt=timezone.now(),
        status__in=['pending', 'viewed']
    ).update(status='dismissed')
    
    return f"Deleted {deleted_count} old recommendations, marked {expired_count} as expired"


@shared_task
def analyze_learning_patterns(student_profile_id, days=30):
    """Analyze learning patterns for a specific student"""
    try:
        student_profile = StudentProfile.objects.get(id=student_profile_id)
        patterns = PerformanceAnalyticsEngine.analyze_learning_patterns(student_profile, days)
        
        # Store patterns in student profile for quick access
        if not student_profile.learning_preferences:
            student_profile.learning_preferences = {}
        
        student_profile.learning_preferences['learning_patterns'] = patterns
        student_profile.learning_preferences['patterns_updated'] = timezone.now().isoformat()
        student_profile.save()
        
        return f"Analyzed learning patterns for {student_profile.user.username}"
        
    except StudentProfile.DoesNotExist:
        return f"Student profile {student_profile_id} not found"
    except Exception as e:
        return f"Error analyzing patterns for student {student_profile_id}: {str(e)}"


@shared_task
def process_session_completion(session_id):
    """Process analytics after a learning session is completed"""
    try:
        from .models import LearningSession
        session = LearningSession.objects.get(id=session_id)
        
        # Update weakness analysis
        WeaknessIdentificationEngine.update_weakness_analysis(session.student)
        
        # Generate session-specific recommendations
        recommendations = RecommendationEngine.generate_comprehensive_recommendations(session.student)
        
        # Create high-priority recommendations based on session performance
        if session.performance_score and session.performance_score < 60:
            # Student struggled, create immediate practice recommendation
            PersonalizedRecommendation.objects.create(
                student=session.student,
                recommendation_type='practice',
                title=f"Review {session.content.original_filename[:30]}...",
                description=f"Your performance was {session.performance_score:.1f}%. Let's review this material to improve understanding.",
                content={
                    'session_id': session.id,
                    'content_id': session.content.id,
                    'performance_score': session.performance_score,
                    'concepts_covered': session.concepts_covered
                },
                priority=4,
                estimated_time_minutes=20,
                related_content=session.content
            )
        
        return f"Processed session completion for {session.student.user.username}"
        
    except Exception as e:
        return f"Error processing session {session_id}: {str(e)}"


@shared_task
def generate_daily_lessons_for_all_students():
    """Generate daily lessons for all active students"""
    from .services import DailyLessonService
    from .models import DailyLesson
    
    # Get students who have been active in the last 14 days or have no lessons yet
    cutoff_date = timezone.now() - timedelta(days=14)
    
    # Students with recent activity
    active_students = StudentProfile.objects.filter(
        learning_sessions__start_time__gte=cutoff_date
    ).distinct()
    
    # Students with no lessons yet (new users)
    students_without_lessons = StudentProfile.objects.exclude(
        daily_lessons__isnull=False
    )
    
    # Combine both querysets
    all_students = active_students.union(students_without_lessons)
    
    today = timezone.now().date()
    total_generated = 0
    total_students = all_students.count()
    
    for student in all_students:
        try:
            # Check if lesson already exists for today
            existing_lesson = DailyLesson.objects.filter(
                student=student,
                lesson_date=today
            ).exists()
            
            if not existing_lesson:
                lesson = DailyLessonService.generate_daily_lesson(student, today)
                if lesson:
                    total_generated += 1
        
        except Exception as e:
            # Log error but continue with other students
            continue
    
    return f"Generated {total_generated} daily lessons for {total_students} students"


@shared_task
def generate_daily_lesson_for_student(student_profile_id, lesson_date=None):
    """Generate a daily lesson for a specific student"""
    try:
        from .services import DailyLessonService
        
        student_profile = StudentProfile.objects.get(id=student_profile_id)
        
        if lesson_date is None:
            lesson_date = timezone.now().date()
        elif isinstance(lesson_date, str):
            from datetime import datetime
            lesson_date = datetime.strptime(lesson_date, '%Y-%m-%d').date()
        
        lesson = DailyLessonService.generate_daily_lesson(student_profile, lesson_date)
        
        if lesson:
            return f"Generated lesson '{lesson.title}' for {student_profile.user.username} on {lesson_date}"
        else:
            return f"Lesson already exists for {student_profile.user.username} on {lesson_date}"
    
    except StudentProfile.DoesNotExist:
        return f"Student profile {student_profile_id} not found"
    except Exception as e:
        return f"Error generating lesson for student {student_profile_id}: {str(e)}"


@shared_task
def update_lesson_streaks():
    """Update learning streaks for all students based on lesson completion"""
    updated_count = 0
    
    for student in StudentProfile.objects.all():
        try:
            old_streak = student.current_streak
            student.update_learning_streak()
            student.save()
            
            if student.current_streak != old_streak:
                updated_count += 1
        
        except Exception as e:
            continue  # Skip problematic students
    
    return f"Updated learning streaks for {updated_count} students"


@shared_task
def cleanup_expired_lessons():
    """Mark old lessons as expired and clean up incomplete lessons"""
    from .models import DailyLesson
    
    # Mark lessons older than 2 days as expired if not completed
    expired_date = timezone.now().date() - timedelta(days=2)
    
    expired_count = DailyLesson.objects.filter(
        lesson_date__lt=expired_date,
        status__in=['scheduled', 'active']
    ).update(status='expired')
    
    return f"Marked {expired_count} old lessons as expired"