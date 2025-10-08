"""
Service class for lesson delivery system functionality including
interactive components, timer tracking, progress validation, and scoring.
"""

from django.utils import timezone
from django.db.models import Avg, Sum, Count
from .models import DailyLesson, LessonProgress
import json
from typing import Dict, List, Optional, Tuple


class LessonDeliveryService:
    """Service for managing lesson delivery, validation, and scoring"""
    
    @staticmethod
    def validate_lesson_completion(lesson: DailyLesson, progress_entries: List[LessonProgress]) -> Tuple[bool, str]:
        """
        Validate if a lesson can be marked as completed based on progress entries
        
        Args:
            lesson: The DailyLesson instance
            progress_entries: List of LessonProgress entries for the lesson
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not lesson:
            return False, "Lesson not found"
            
        if lesson.status != 'active':
            return False, f"Lesson is not active (current status: {lesson.status})"
        
        # Get expected activities from lesson structure
        activities = lesson.get_lesson_activities()
        expected_activity_count = len(activities)
        
        if expected_activity_count == 0:
            return True, ""  # No activities to validate
        
        # Check if all required activities have progress entries
        completed_activities = set(progress.activity_index for progress in progress_entries)
        required_activities = set(range(expected_activity_count))
        
        missing_activities = required_activities - completed_activities
        if missing_activities:
            return False, f"Missing progress for activities: {sorted(missing_activities)}"
        
        # Validate specific activity types
        for progress in progress_entries:
            activity_index = progress.activity_index
            if activity_index < len(activities):
                activity = activities[activity_index]
                validation_result = LessonDeliveryService._validate_activity_progress(
                    activity, progress
                )
                if not validation_result[0]:
                    return validation_result
        
        return True, ""
    
    @staticmethod
    def _validate_activity_progress(activity: Dict, progress: LessonProgress) -> Tuple[bool, str]:
        """Validate progress for a specific activity type"""
        activity_type = activity.get('type', '')
        
        if activity_type == 'quiz':
            # Quiz activities should have answers recorded
            if not progress.student_answer:
                return False, f"No answers recorded for quiz activity {progress.activity_index}"
            
            try:
                answers = json.loads(progress.student_answer)
                if not isinstance(answers, list) or len(answers) == 0:
                    return False, f"Invalid quiz answers for activity {progress.activity_index}"
            except json.JSONDecodeError:
                return False, f"Invalid quiz answer format for activity {progress.activity_index}"
        
        elif activity_type == 'reflection':
            # Reflection activities should have minimum word count
            if not progress.student_answer:
                return False, f"No reflection text provided for activity {progress.activity_index}"
            
            min_words = activity.get('min_words', 10)
            word_count = len(progress.student_answer.strip().split())
            if word_count < min_words:
                return False, f"Reflection too short for activity {progress.activity_index} (minimum {min_words} words)"
        
        elif activity_type == 'flashcard':
            # Flashcard activities should have difficulty ratings
            if not progress.student_answer:
                return False, f"No flashcard ratings recorded for activity {progress.activity_index}"
            
            try:
                ratings = json.loads(progress.student_answer)
                if not isinstance(ratings, list):
                    return False, f"Invalid flashcard ratings for activity {progress.activity_index}"
            except json.JSONDecodeError:
                return False, f"Invalid flashcard rating format for activity {progress.activity_index}"
        
        return True, ""
    
    @staticmethod
    def calculate_lesson_score(lesson: DailyLesson, progress_entries: List[LessonProgress]) -> float:
        """
        Calculate overall lesson performance score based on activity progress
        
        Args:
            lesson: The DailyLesson instance
            progress_entries: List of LessonProgress entries
            
        Returns:
            Performance score as percentage (0-100)
        """
        if not progress_entries:
            return 0.0
        
        activities = lesson.get_lesson_activities()
        total_score = 0.0
        total_weight = 0.0
        
        for progress in progress_entries:
            activity_index = progress.activity_index
            if activity_index < len(activities):
                activity = activities[activity_index]
                activity_score = LessonDeliveryService._calculate_activity_score(
                    activity, progress
                )
                activity_weight = activity.get('weight', 1.0)
                
                total_score += activity_score * activity_weight
                total_weight += activity_weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    @staticmethod
    def _calculate_activity_score(activity: Dict, progress: LessonProgress) -> float:
        """Calculate score for a specific activity"""
        activity_type = activity.get('type', '')
        
        if activity_type == 'quiz':
            return LessonDeliveryService._calculate_quiz_score(activity, progress)
        elif activity_type == 'flashcard':
            return LessonDeliveryService._calculate_flashcard_score(activity, progress)
        elif activity_type == 'reflection':
            return LessonDeliveryService._calculate_reflection_score(activity, progress)
        else:
            # Reading activities get full score for completion
            return 100.0
    
    @staticmethod
    def _calculate_quiz_score(activity: Dict, progress: LessonProgress) -> float:
        """Calculate score for quiz activity"""
        if not progress.student_answer:
            return 0.0
        
        try:
            answers = json.loads(progress.student_answer)
            if not isinstance(answers, list):
                return 0.0
            
            correct_count = sum(1 for answer in answers if answer.get('correct', False))
            total_questions = len(answers)
            
            if total_questions == 0:
                return 0.0
            
            base_score = (correct_count / total_questions) * 100
            
            # Apply time bonus/penalty
            time_bonus = LessonDeliveryService._calculate_time_bonus(
                progress.time_spent_seconds, 
                activity.get('estimated_time', 120)  # Default 2 minutes
            )
            
            return min(100.0, base_score + time_bonus)
            
        except (json.JSONDecodeError, KeyError):
            return 0.0
    
    @staticmethod
    def _calculate_flashcard_score(activity: Dict, progress: LessonProgress) -> float:
        """Calculate score for flashcard activity"""
        if not progress.student_answer:
            return 0.0
        
        try:
            ratings = json.loads(progress.student_answer)
            if not isinstance(ratings, list):
                return 0.0
            
            # Convert difficulty ratings to scores
            rating_scores = {
                'easy': 100,
                'medium': 75,
                'hard': 50
            }
            
            total_score = sum(rating_scores.get(rating, 50) for rating in ratings)
            return total_score / len(ratings) if ratings else 0.0
            
        except (json.JSONDecodeError, KeyError):
            return 0.0
    
    @staticmethod
    def _calculate_reflection_score(activity: Dict, progress: LessonProgress) -> float:
        """Calculate score for reflection activity"""
        if not progress.student_answer:
            return 0.0
        
        min_words = activity.get('min_words', 10)
        word_count = len(progress.student_answer.strip().split())
        
        if word_count < min_words:
            return (word_count / min_words) * 60  # Partial credit up to 60%
        
        # Full score for meeting minimum, bonus for exceeding
        base_score = 100.0
        if word_count > min_words * 2:
            base_score = min(110.0, base_score + 10)  # 10% bonus for detailed reflection
        
        return min(100.0, base_score)
    
    @staticmethod
    def _calculate_time_bonus(actual_seconds: int, estimated_seconds: int) -> float:
        """Calculate time-based bonus/penalty"""
        if estimated_seconds <= 0:
            return 0.0
        
        time_ratio = actual_seconds / estimated_seconds
        
        if time_ratio <= 0.8:  # Completed quickly
            return 5.0  # 5% bonus
        elif time_ratio <= 1.2:  # Within expected time
            return 0.0  # No bonus/penalty
        elif time_ratio <= 2.0:  # Took longer than expected
            return -2.0  # 2% penalty
        else:  # Took much longer
            return -5.0  # 5% penalty
    
    @staticmethod
    def calculate_xp_earned(lesson: DailyLesson, performance_score: float, completion_ratio: float) -> int:
        """
        Calculate XP earned based on lesson performance and completion
        
        Args:
            lesson: The DailyLesson instance
            performance_score: Performance score (0-100)
            completion_ratio: Ratio of completed activities (0-1)
            
        Returns:
            XP points earned
        """
        base_xp = 10  # Base XP for attempting a lesson
        
        # Performance bonus (0-10 XP based on score)
        performance_bonus = int(performance_score / 10)
        
        # Completion bonus (0-5 XP based on completion ratio)
        completion_bonus = int(completion_ratio * 5)
        
        # Lesson type multiplier
        type_multipliers = {
            'review': 1.0,
            'new_content': 1.2,
            'weakness_focus': 1.3,
            'mixed': 1.1,
            'assessment': 1.5
        }
        multiplier = type_multipliers.get(lesson.lesson_type, 1.0)
        
        # Difficulty multiplier
        difficulty_multipliers = {
            'beginner': 0.9,
            'intermediate': 1.0,
            'advanced': 1.2
        }
        difficulty_multiplier = difficulty_multipliers.get(lesson.difficulty_level, 1.0)
        
        total_xp = (base_xp + performance_bonus + completion_bonus) * multiplier * difficulty_multiplier
        
        return max(5, int(total_xp))  # Minimum 5 XP
    
    @staticmethod
    def get_lesson_analytics(lesson: DailyLesson) -> Dict:
        """Get comprehensive analytics for a completed lesson"""
        progress_entries = LessonProgress.objects.filter(lesson=lesson).order_by('activity_index')
        
        analytics = {
            'lesson_id': lesson.id,
            'title': lesson.title,
            'lesson_date': lesson.lesson_date.isoformat(),
            'status': lesson.status,
            'performance_score': lesson.performance_score or 0,
            'time_spent_minutes': lesson.time_spent_minutes,
            'xp_earned': lesson.xp_earned,
            'difficulty_level': lesson.difficulty_level,
            'lesson_type': lesson.lesson_type,
            'activities': [],
            'concepts_covered': list(set(progress.concept for progress in progress_entries if progress.concept)),
            'total_activities': len(lesson.get_lesson_activities()),
            'completed_activities': progress_entries.count(),
            'average_time_per_activity': 0,
            'difficulty_distribution': {}
        }
        
        # Activity-level analytics
        total_time = 0
        difficulty_counts = {'easy': 0, 'medium': 0, 'hard': 0}
        
        for progress in progress_entries:
            activity_data = {
                'activity_index': progress.activity_index,
                'activity_type': progress.activity_type,
                'concept': progress.concept,
                'is_correct': progress.is_correct,
                'time_spent_seconds': progress.time_spent_seconds,
                'difficulty_rating': progress.difficulty_rating
            }
            analytics['activities'].append(activity_data)
            
            total_time += progress.time_spent_seconds
            if progress.difficulty_rating in difficulty_counts:
                difficulty_counts[progress.difficulty_rating] += 1
        
        # Calculate averages
        if progress_entries.count() > 0:
            analytics['average_time_per_activity'] = total_time / progress_entries.count()
        
        analytics['difficulty_distribution'] = difficulty_counts
        
        return analytics
    
    @staticmethod
    def get_student_lesson_stats(student_profile) -> Dict:
        """Get comprehensive lesson statistics for a student"""
        lessons = DailyLesson.objects.filter(student=student_profile)
        completed_lessons = lessons.filter(status='completed')
        
        stats = {
            'total_lessons': lessons.count(),
            'completed_lessons': completed_lessons.count(),
            'skipped_lessons': lessons.filter(status='skipped').count(),
            'completion_rate': 0,
            'average_score': 0,
            'total_xp': 0,
            'total_time_minutes': 0,
            'current_streak': 0,
            'longest_streak': 0,
            'lesson_types': {},
            'difficulty_levels': {},
            'recent_performance': []
        }
        
        if lessons.count() > 0:
            stats['completion_rate'] = (completed_lessons.count() / lessons.count()) * 100
        
        if completed_lessons.exists():
            # Calculate averages
            aggregates = completed_lessons.aggregate(
                avg_score=Avg('performance_score'),
                total_xp=Sum('xp_earned'),
                total_time=Sum('time_spent_minutes')
            )
            
            stats['average_score'] = aggregates['avg_score'] or 0
            stats['total_xp'] = aggregates['total_xp'] or 0
            stats['total_time_minutes'] = aggregates['total_time'] or 0
            
            # Lesson type distribution
            type_counts = completed_lessons.values('lesson_type').annotate(
                count=Count('id')
            ).order_by('-count')
            stats['lesson_types'] = {item['lesson_type']: item['count'] for item in type_counts}
            
            # Difficulty level distribution
            difficulty_counts = completed_lessons.values('difficulty_level').annotate(
                count=Count('id')
            ).order_by('-count')
            stats['difficulty_levels'] = {item['difficulty_level']: item['count'] for item in difficulty_counts}
            
            # Recent performance (last 10 lessons)
            recent_lessons = completed_lessons.order_by('-lesson_date')[:10]
            stats['recent_performance'] = [
                {
                    'date': lesson.lesson_date.isoformat(),
                    'score': lesson.performance_score or 0,
                    'xp': lesson.xp_earned,
                    'time': lesson.time_spent_minutes
                }
                for lesson in recent_lessons
            ]
        
        # Calculate streaks
        streak_info = LessonDeliveryService._calculate_lesson_streaks(student_profile)
        stats.update(streak_info)
        
        return stats
    
    @staticmethod
    def _calculate_lesson_streaks(student_profile) -> Dict:
        """Calculate current and longest lesson completion streaks"""
        from datetime import timedelta
        
        today = timezone.now().date()
        current_streak = 0
        longest_streak = 0
        temp_streak = 0
        
        # Get lessons from the past 60 days
        lessons = DailyLesson.objects.filter(
            student=student_profile,
            lesson_date__gte=today - timedelta(days=60)
        ).order_by('-lesson_date')
        
        # Calculate current streak (consecutive days from today backwards)
        for lesson in lessons:
            expected_date = today - timedelta(days=current_streak)
            if lesson.lesson_date == expected_date and lesson.status == 'completed':
                current_streak += 1
            else:
                break
        
        # Calculate longest streak
        consecutive_days = []
        for lesson in lessons.filter(status='completed').order_by('lesson_date'):
            consecutive_days.append(lesson.lesson_date)
        
        if consecutive_days:
            temp_streak = 1
            for i in range(1, len(consecutive_days)):
                if consecutive_days[i] == consecutive_days[i-1] + timedelta(days=1):
                    temp_streak += 1
                    longest_streak = max(longest_streak, temp_streak)
                else:
                    temp_streak = 1
            longest_streak = max(longest_streak, temp_streak)
        
        return {
            'current_streak': current_streak,
            'longest_streak': longest_streak
        }