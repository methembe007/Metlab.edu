"""
Learning session tracking and management services
"""
from django.utils import timezone
from django.db.models import Avg, Count, Q, Sum
from django.db import models
from .models import LearningSession, WeaknessAnalysis, PersonalizedRecommendation, DailyLesson, LessonProgress
from .analytics import (
    PerformanceAnalyticsEngine, 
    WeaknessIdentificationEngine, 
    AdaptiveDifficultyEngine,
    RecommendationEngine
)
from accounts.models import StudentProfile
from content.models import UploadedContent


class LearningSessionService:
    """Service for managing learning sessions and tracking"""
    
    @staticmethod
    def start_session(student_profile, content, session_type='mixed', difficulty_level='intermediate'):
        """Start a new learning session for a student"""
        # End any active sessions for this student first
        LearningSessionService.end_active_sessions(student_profile)
        
        session = LearningSession.objects.create(
            student=student_profile,
            content=content,
            session_type=session_type,
            difficulty_level=difficulty_level,
            status='active'
        )
        return session
    
    @staticmethod
    def end_active_sessions(student_profile):
        """End all active sessions for a student"""
        active_sessions = LearningSession.objects.filter(
            student=student_profile,
            status='active'
        )
        
        for session in active_sessions:
            session.end_session()
    
    @staticmethod
    def update_session_progress(session_id, questions_attempted=0, questions_correct=0, concepts_covered=None):
        """Update progress for an active learning session"""
        try:
            session = LearningSession.objects.get(id=session_id, status='active')
            
            session.questions_attempted += questions_attempted
            session.questions_correct += questions_correct
            
            if concepts_covered:
                # Merge new concepts with existing ones
                existing_concepts = set(session.concepts_covered)
                new_concepts = set(concepts_covered) if isinstance(concepts_covered, list) else {concepts_covered}
                session.concepts_covered = list(existing_concepts.union(new_concepts))
            
            session.calculate_performance_score()
            session.save()
            
            return session
        except LearningSession.DoesNotExist:
            return None
    
    @staticmethod
    def complete_session(session_id, xp_earned=0):
        """Complete a learning session and calculate final metrics"""
        try:
            session = LearningSession.objects.get(id=session_id)
            session.xp_earned = xp_earned
            session.end_session()
            
            # Update student's total XP
            session.student.total_xp += xp_earned
            session.student.save()
            
            # Trigger background analytics processing
            try:
                from .tasks import process_session_completion
                process_session_completion.delay(session_id)
            except ImportError:
                # Fallback to synchronous processing if Celery is not available
                WeaknessIdentificationEngine.update_weakness_analysis(session.student)
                RecommendationService.generate_session_based_recommendations(session)
            
            return session
        except LearningSession.DoesNotExist:
            return None
    
    @staticmethod
    def get_student_sessions(student_profile, limit=10):
        """Get recent learning sessions for a student"""
        return LearningSession.objects.filter(
            student=student_profile
        ).order_by('-start_time')[:limit]
    
    @staticmethod
    def get_session_statistics(student_profile, days=30):
        """Get learning session statistics for a student"""
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        sessions = LearningSession.objects.filter(
            student=student_profile,
            start_time__gte=cutoff_date,
            status='completed'
        )
        
        stats = sessions.aggregate(
            total_sessions=Count('id'),
            avg_performance=Avg('performance_score'),
            total_time=Sum('time_spent_minutes'),
            total_questions=Sum('questions_attempted'),
            total_correct=Sum('questions_correct')
        )
        
        # Calculate overall accuracy
        if stats['total_questions'] and stats['total_questions'] > 0:
            stats['overall_accuracy'] = (stats['total_correct'] / stats['total_questions']) * 100
        else:
            stats['overall_accuracy'] = 0
        
        return stats


class WeaknessAnalysisService:
    """Service for analyzing student weaknesses and learning gaps"""
    
    @staticmethod
    def update_from_session(session):
        """Update weakness analysis based on a completed learning session"""
        if not session.concepts_covered:
            return
        
        for concept in session.concepts_covered:
            weakness, created = WeaknessAnalysis.objects.get_or_create(
                student=session.student,
                subject=session.content.subject or 'General',
                concept=concept,
                defaults={
                    'weakness_score': 50.0,
                    'weakness_level': 'medium',
                    'total_attempts': 0,
                    'correct_attempts': 0,
                }
            )
            
            # Update attempts based on session performance
            concept_questions = session.questions_attempted // len(session.concepts_covered)
            concept_correct = int((session.questions_correct / session.questions_attempted) * concept_questions) if session.questions_attempted > 0 else 0
            
            weakness.total_attempts += concept_questions
            weakness.correct_attempts += concept_correct
            weakness.last_attempt_score = session.performance_score
            weakness.calculate_weakness_score()
            weakness.save()
    
    @staticmethod
    def get_student_weaknesses(student_profile, limit=10):
        """Get top weaknesses for a student"""
        return WeaknessAnalysis.objects.filter(
            student=student_profile
        ).order_by('-priority_level', '-weakness_score')[:limit]
    
    @staticmethod
    def get_critical_weaknesses(student_profile):
        """Get critical weaknesses that need immediate attention"""
        return WeaknessAnalysis.objects.filter(
            student=student_profile,
            weakness_level='critical'
        ).order_by('-weakness_score')
    
    @staticmethod
    def analyze_improvement_trends(student_profile):
        """Analyze improvement trends for a student's weaknesses"""
        weaknesses = WeaknessAnalysis.objects.filter(student=student_profile)
        
        trends = {
            'improving': weaknesses.filter(improvement_trend='improving').count(),
            'stable': weaknesses.filter(improvement_trend='stable').count(),
            'declining': weaknesses.filter(improvement_trend='declining').count(),
        }
        
        return trends


class RecommendationService:
    """Service for generating and managing personalized recommendations"""
    
    @staticmethod
    def generate_weakness_recommendations(student_profile):
        """Generate recommendations based on student weaknesses"""
        critical_weaknesses = WeaknessAnalysisService.get_critical_weaknesses(student_profile)
        recommendations = []
        
        for weakness in critical_weaknesses[:3]:  # Top 3 critical weaknesses
            # Check if recommendation already exists
            existing = PersonalizedRecommendation.objects.filter(
                student=student_profile,
                related_weakness=weakness,
                status__in=['pending', 'viewed', 'accepted']
            ).exists()
            
            if not existing:
                recommendation = PersonalizedRecommendation.objects.create(
                    student=student_profile,
                    recommendation_type='practice',
                    title=f"Practice {weakness.concept}",
                    description=f"You've shown difficulty with {weakness.concept}. Let's practice this concept to improve your understanding.",
                    content={
                        'concept': weakness.concept,
                        'subject': weakness.subject,
                        'weakness_score': weakness.weakness_score,
                        'suggested_practice_time': 15
                    },
                    priority=weakness.priority_level,
                    related_weakness=weakness,
                    estimated_time_minutes=15
                )
                recommendations.append(recommendation)
        
        return recommendations
    
    @staticmethod
    def generate_content_recommendations(student_profile):
        """Generate content recommendations based on learning history"""
        # Get subjects the student has been studying
        recent_sessions = LearningSession.objects.filter(
            student=student_profile,
            status='completed'
        ).order_by('-start_time')[:10]
        
        studied_subjects = set()
        for session in recent_sessions:
            if session.content.subject:
                studied_subjects.add(session.content.subject)
        
        recommendations = []
        
        # Recommend new content in studied subjects
        for subject in studied_subjects:
            # Find content the student hasn't studied yet
            unstudied_content = UploadedContent.objects.filter(
                subject=subject,
                processing_status='completed'
            ).exclude(
                learning_sessions__student=student_profile
            ).first()
            
            if unstudied_content:
                recommendation = PersonalizedRecommendation.objects.create(
                    student=student_profile,
                    recommendation_type='content',
                    title=f"New {subject} Content Available",
                    description=f"Check out this new {subject} material: {unstudied_content.original_filename}",
                    content={
                        'content_id': unstudied_content.id,
                        'subject': subject,
                        'filename': unstudied_content.original_filename
                    },
                    priority=2,
                    related_content=unstudied_content,
                    estimated_time_minutes=20
                )
                recommendations.append(recommendation)
        
        return recommendations
    
    @staticmethod
    def generate_study_plan_recommendation(student_profile):
        """Generate a personalized study plan recommendation"""
        weaknesses = WeaknessAnalysisService.get_student_weaknesses(student_profile, limit=5)
        
        if weaknesses:
            study_plan = {
                'daily_goals': [],
                'weekly_focus': [],
                'priority_concepts': []
            }
            
            for weakness in weaknesses:
                study_plan['priority_concepts'].append({
                    'concept': weakness.concept,
                    'subject': weakness.subject,
                    'priority': weakness.priority_level,
                    'recommended_time': 10 + (weakness.priority_level * 5)
                })
            
            recommendation = PersonalizedRecommendation.objects.create(
                student=student_profile,
                recommendation_type='study_plan',
                title="Personalized Study Plan",
                description="A customized study plan based on your learning patterns and areas for improvement.",
                content=study_plan,
                priority=4,
                estimated_time_minutes=30
            )
            
            return recommendation
        
        return None
    
    @staticmethod
    def get_active_recommendations(student_profile, limit=5):
        """Get active recommendations for a student"""
        return PersonalizedRecommendation.objects.filter(
            student=student_profile,
            status__in=['pending', 'viewed', 'accepted']
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        ).order_by('-priority', '-created_at')[:limit]
    
    @staticmethod
    def mark_recommendation_viewed(recommendation_id):
        """Mark a recommendation as viewed"""
        try:
            recommendation = PersonalizedRecommendation.objects.get(id=recommendation_id)
            recommendation.mark_viewed()
            return recommendation
        except PersonalizedRecommendation.DoesNotExist:
            return None
    
    @staticmethod
    def generate_session_based_recommendations(session):
        """Generate recommendations based on a completed learning session"""
        student_profile = session.student
        
        # Generate comprehensive recommendations using the advanced engine
        advanced_recommendations = RecommendationEngine.generate_comprehensive_recommendations(student_profile)
        
        created_recommendations = []
        for rec_data in advanced_recommendations[:5]:  # Limit to top 5
            # Check if similar recommendation already exists
            existing = PersonalizedRecommendation.objects.filter(
                student=student_profile,
                recommendation_type=rec_data['type'],
                title=rec_data['title'],
                status__in=['pending', 'viewed', 'accepted']
            ).exists()
            
            if not existing:
                recommendation = PersonalizedRecommendation.objects.create(
                    student=student_profile,
                    recommendation_type=rec_data['type'],
                    title=rec_data['title'],
                    description=rec_data['description'],
                    content=rec_data['content'],
                    priority=rec_data['priority'],
                    estimated_time_minutes=rec_data['estimated_time']
                )
                created_recommendations.append(recommendation)
        
        return created_recommendations
    
    @staticmethod
    def get_performance_insights(student_profile):
        """Get detailed performance insights for a student"""
        return PerformanceAnalyticsEngine.analyze_learning_patterns(student_profile)
    
    @staticmethod
    def get_adaptive_difficulty_recommendation(student_profile, content_subject=None):
        """Get adaptive difficulty recommendation for new content"""
        return AdaptiveDifficultyEngine.recommend_difficulty(student_profile, content_subject)


class DailyLessonService:
    """Service for generating and managing daily personalized lessons"""
    
    @staticmethod
    def generate_daily_lesson(student_profile, lesson_date=None):
        """Generate a personalized daily lesson for a student"""
        if lesson_date is None:
            lesson_date = timezone.now().date()
        
        # Check if lesson already exists for this date
        existing_lesson = DailyLesson.objects.filter(
            student=student_profile,
            lesson_date=lesson_date
        ).first()
        
        if existing_lesson:
            return existing_lesson
        
        # Analyze student's learning patterns and weaknesses
        lesson_plan = DailyLessonService._create_lesson_plan(student_profile)
        
        # Create the daily lesson
        lesson = DailyLesson.objects.create(
            student=student_profile,
            lesson_date=lesson_date,
            lesson_type=lesson_plan['type'],
            title=lesson_plan['title'],
            description=lesson_plan['description'],
            content_structure=lesson_plan['content_structure'],
            estimated_duration_minutes=lesson_plan['duration'],
            difficulty_level=lesson_plan['difficulty'],
            priority_concepts=lesson_plan['concepts']
        )
        
        # Link related content and weaknesses
        if lesson_plan.get('related_content'):
            lesson.related_content.set(lesson_plan['related_content'])
        
        if lesson_plan.get('related_weaknesses'):
            lesson.related_weaknesses.set(lesson_plan['related_weaknesses'])
        
        return lesson
    
    @staticmethod
    def _create_lesson_plan(student_profile):
        """Create a personalized lesson plan based on student's progress and weaknesses"""
        # Get student's recent performance and weaknesses
        recent_sessions = LearningSession.objects.filter(
            student=student_profile,
            status='completed'
        ).order_by('-start_time')[:10]
        
        weaknesses = WeaknessAnalysis.objects.filter(
            student=student_profile
        ).order_by('-priority_level', '-weakness_score')[:5]
        
        # Determine lesson type based on student's needs
        lesson_type = DailyLessonService._determine_lesson_type(student_profile, weaknesses)
        
        # Get available content for the lesson
        available_content = UploadedContent.objects.filter(
            processing_status='completed'
        )
        
        if lesson_type == 'weakness_focus' and weaknesses:
            return DailyLessonService._create_weakness_focused_lesson(
                student_profile, weaknesses, available_content
            )
        elif lesson_type == 'review':
            return DailyLessonService._create_review_lesson(
                student_profile, recent_sessions, available_content
            )
        elif lesson_type == 'new_content':
            return DailyLessonService._create_new_content_lesson(
                student_profile, available_content
            )
        else:  # mixed
            return DailyLessonService._create_mixed_lesson(
                student_profile, weaknesses, available_content
            )
    
    @staticmethod
    def _determine_lesson_type(student_profile, weaknesses):
        """Determine the best lesson type for the student"""
        # Check if student has critical weaknesses
        critical_weaknesses = [w for w in weaknesses if w.weakness_level == 'critical']
        if critical_weaknesses:
            return 'weakness_focus'
        
        # Check recent lesson completion rate
        recent_lessons = DailyLesson.objects.filter(
            student=student_profile,
            lesson_date__gte=timezone.now().date() - timezone.timedelta(days=7)
        )
        
        completed_count = recent_lessons.filter(status='completed').count()
        total_count = recent_lessons.count()
        
        if total_count > 0:
            completion_rate = completed_count / total_count
            if completion_rate < 0.5:
                return 'review'  # Focus on review if struggling
        
        # Check if student needs new content
        recent_content_ids = set()
        for session in LearningSession.objects.filter(
            student=student_profile
        ).order_by('-start_time')[:20]:
            recent_content_ids.add(session.content.id)
        
        unused_content = UploadedContent.objects.filter(
            processing_status='completed'
        ).exclude(id__in=recent_content_ids)
        
        if unused_content.exists():
            return 'new_content'
        
        return 'mixed'
    
    @staticmethod
    def _create_weakness_focused_lesson(student_profile, weaknesses, available_content):
        """Create a lesson focused on addressing student weaknesses"""
        primary_weakness = weaknesses[0]
        
        # Find content related to the weakness
        related_content = available_content.filter(
            key_concepts__icontains=primary_weakness.concept
        )[:2]
        
        activities = []
        
        # Add review activity for the weak concept
        activities.append({
            'type': 'review',
            'title': f"Review: {primary_weakness.concept}",
            'concept': primary_weakness.concept,
            'description': f"Let's review the concept of {primary_weakness.concept}",
            'estimated_time': 3
        })
        
        # Add practice questions
        activities.append({
            'type': 'quiz',
            'title': f"Practice Questions: {primary_weakness.concept}",
            'concept': primary_weakness.concept,
            'question_count': 3,
            'difficulty': 'medium' if primary_weakness.weakness_score > 60 else 'easy',
            'estimated_time': 5
        })
        
        # Add flashcard review
        activities.append({
            'type': 'flashcard',
            'title': f"Flashcard Review: {primary_weakness.concept}",
            'concept': primary_weakness.concept,
            'card_count': 5,
            'estimated_time': 2
        })
        
        return {
            'type': 'weakness_focus',
            'title': f"Focus on {primary_weakness.concept}",
            'description': f"Today's lesson focuses on improving your understanding of {primary_weakness.concept}",
            'content_structure': {
                'activities': activities,
                'materials': [{'type': 'concept_review', 'concept': primary_weakness.concept}]
            },
            'duration': 10,
            'difficulty': 'medium',
            'concepts': [primary_weakness.concept],
            'related_content': list(related_content),
            'related_weaknesses': [primary_weakness]
        }
    
    @staticmethod
    def _create_review_lesson(student_profile, recent_sessions, available_content):
        """Create a review lesson based on recent learning sessions"""
        # Get concepts from recent sessions
        recent_concepts = set()
        for session in recent_sessions[:5]:
            recent_concepts.update(session.concepts_covered)
        
        if not recent_concepts:
            return DailyLessonService._create_mixed_lesson(student_profile, [], available_content)
        
        primary_concept = list(recent_concepts)[0]
        
        activities = []
        
        # Add quick review
        activities.append({
            'type': 'reading',
            'title': f"Quick Review: {primary_concept}",
            'concept': primary_concept,
            'description': f"Let's quickly review what you learned about {primary_concept}",
            'estimated_time': 2
        })
        
        # Add mixed practice
        activities.append({
            'type': 'quiz',
            'title': "Mixed Practice Questions",
            'concepts': list(recent_concepts)[:3],
            'question_count': 4,
            'difficulty': 'medium',
            'estimated_time': 6
        })
        
        # Add reflection
        activities.append({
            'type': 'reflection',
            'title': "Learning Reflection",
            'description': "Think about what you've learned and what you'd like to focus on next",
            'estimated_time': 2
        })
        
        return {
            'type': 'review',
            'title': "Review Your Recent Learning",
            'description': "Today's lesson reviews concepts you've been studying recently",
            'content_structure': {
                'activities': activities,
                'materials': [{'type': 'review_summary', 'concepts': list(recent_concepts)}]
            },
            'duration': 10,
            'difficulty': 'medium',
            'concepts': list(recent_concepts),
            'related_content': [],
            'related_weaknesses': []
        }
    
    @staticmethod
    def _create_new_content_lesson(student_profile, available_content):
        """Create a lesson introducing new content"""
        # Find content the student hasn't studied
        studied_content_ids = set(
            LearningSession.objects.filter(
                student=student_profile
            ).values_list('content_id', flat=True)
        )
        
        new_content = available_content.exclude(
            id__in=studied_content_ids
        ).first()
        
        if not new_content:
            return DailyLessonService._create_mixed_lesson(student_profile, [], available_content)
        
        # Extract key concepts from the new content
        key_concepts = new_content.key_concepts or []
        primary_concept = key_concepts[0] if key_concepts else "New Topic"
        
        activities = []
        
        # Add introduction
        activities.append({
            'type': 'reading',
            'title': f"Introduction to {primary_concept}",
            'concept': primary_concept,
            'content_id': new_content.id,
            'description': f"Let's explore a new topic: {primary_concept}",
            'estimated_time': 4
        })
        
        # Add comprehension questions
        activities.append({
            'type': 'quiz',
            'title': "Understanding Check",
            'concept': primary_concept,
            'content_id': new_content.id,
            'question_count': 3,
            'difficulty': 'easy',
            'estimated_time': 4
        })
        
        # Add summary
        activities.append({
            'type': 'reflection',
            'title': "Key Takeaways",
            'description': f"What are the main points about {primary_concept}?",
            'estimated_time': 2
        })
        
        return {
            'type': 'new_content',
            'title': f"Explore: {new_content.original_filename}",
            'description': f"Today's lesson introduces new content from {new_content.original_filename}",
            'content_structure': {
                'activities': activities,
                'materials': [{'type': 'content', 'content_id': new_content.id}]
            },
            'duration': 10,
            'difficulty': 'intermediate',
            'concepts': key_concepts[:3],
            'related_content': [new_content],
            'related_weaknesses': []
        }
    
    @staticmethod
    def _create_mixed_lesson(student_profile, weaknesses, available_content):
        """Create a mixed lesson with various activities"""
        activities = []
        concepts = []
        
        # Add a quick warm-up
        activities.append({
            'type': 'flashcard',
            'title': "Quick Warm-up",
            'description': "Review some key concepts to get started",
            'card_count': 3,
            'estimated_time': 2
        })
        
        # Add main practice
        if weaknesses:
            primary_weakness = weaknesses[0]
            concepts.append(primary_weakness.concept)
            activities.append({
                'type': 'quiz',
                'title': f"Practice: {primary_weakness.concept}",
                'concept': primary_weakness.concept,
                'question_count': 3,
                'difficulty': 'medium',
                'estimated_time': 5
            })
        else:
            activities.append({
                'type': 'quiz',
                'title': "Mixed Practice",
                'description': "Practice questions from various topics",
                'question_count': 4,
                'difficulty': 'medium',
                'estimated_time': 5
            })
        
        # Add closing activity
        activities.append({
            'type': 'reflection',
            'title': "Daily Reflection",
            'description': "How did today's practice go?",
            'estimated_time': 3
        })
        
        return {
            'type': 'mixed',
            'title': "Daily Practice Session",
            'description': "A balanced mix of review, practice, and reflection",
            'content_structure': {
                'activities': activities,
                'materials': [{'type': 'mixed_practice'}]
            },
            'duration': 10,
            'difficulty': 'medium',
            'concepts': concepts,
            'related_content': [],
            'related_weaknesses': weaknesses[:1] if weaknesses else []
        }
    
    @staticmethod
    def get_student_daily_lesson(student_profile, lesson_date=None):
        """Get or generate the daily lesson for a student"""
        if lesson_date is None:
            lesson_date = timezone.now().date()
        
        lesson = DailyLesson.objects.filter(
            student=student_profile,
            lesson_date=lesson_date
        ).first()
        
        if not lesson:
            lesson = DailyLessonService.generate_daily_lesson(student_profile, lesson_date)
        
        return lesson
    
    @staticmethod
    def start_lesson(lesson_id):
        """Start a daily lesson"""
        try:
            lesson = DailyLesson.objects.get(id=lesson_id)
            lesson.start_lesson()
            return lesson
        except DailyLesson.DoesNotExist:
            return None
    
    @staticmethod
    def complete_lesson(lesson_id, performance_data=None):
        """Complete a daily lesson with performance tracking"""
        try:
            lesson = DailyLesson.objects.get(id=lesson_id)
            
            # Calculate performance score and XP
            performance_score = 0
            xp_earned = 10  # Base XP
            
            if performance_data:
                total_activities = len(performance_data.get('activities', []))
                correct_activities = sum(1 for activity in performance_data.get('activities', []) 
                                       if activity.get('is_correct', False))
                
                if total_activities > 0:
                    performance_score = (correct_activities / total_activities) * 100
                    # Bonus XP for good performance
                    if performance_score >= 80:
                        xp_earned += 5
                    elif performance_score >= 60:
                        xp_earned += 3
            
            lesson.complete_lesson(performance_score, xp_earned)
            
            # Create progress entries for detailed tracking
            if performance_data and performance_data.get('activities'):
                for i, activity_data in enumerate(performance_data['activities']):
                    LessonProgress.objects.create(
                        lesson=lesson,
                        activity_type=activity_data.get('type', 'practice'),
                        activity_index=i,
                        concept=activity_data.get('concept', ''),
                        question_text=activity_data.get('question', ''),
                        student_answer=activity_data.get('student_answer', ''),
                        correct_answer=activity_data.get('correct_answer', ''),
                        is_correct=activity_data.get('is_correct'),
                        time_spent_seconds=activity_data.get('time_spent', 0)
                    )
            
            return lesson
        except DailyLesson.DoesNotExist:
            return None
    
    @staticmethod
    def get_lesson_recommendations(student_profile, days_ahead=7):
        """Generate lesson recommendations for upcoming days"""
        recommendations = []
        current_date = timezone.now().date()
        
        for i in range(1, days_ahead + 1):
            future_date = current_date + timezone.timedelta(days=i)
            
            # Check if lesson already exists
            existing_lesson = DailyLesson.objects.filter(
                student=student_profile,
                lesson_date=future_date
            ).first()
            
            if not existing_lesson:
                # Generate a preview of what the lesson would be
                lesson_plan = DailyLessonService._create_lesson_plan(student_profile)
                recommendations.append({
                    'date': future_date,
                    'type': lesson_plan['type'],
                    'title': lesson_plan['title'],
                    'concepts': lesson_plan['concepts'],
                    'duration': lesson_plan['duration']
                })
        
        return recommendations
    
    @staticmethod
    def get_lesson_completion_stats(student_profile, days=30):
        """Get lesson completion statistics for a student"""
        from datetime import timedelta
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        lessons = DailyLesson.objects.filter(
            student=student_profile,
            lesson_date__range=[start_date, end_date]
        )
        
        total_lessons = lessons.count()
        completed_lessons = lessons.filter(status='completed').count()
        avg_performance = lessons.filter(
            status='completed',
            performance_score__isnull=False
        ).aggregate(avg_score=models.Avg('performance_score'))['avg_score'] or 0
        
        total_xp = lessons.filter(status='completed').aggregate(
            total=models.Sum('xp_earned')
        )['total'] or 0
        
        return {
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'completion_rate': (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0,
            'average_performance': round(avg_performance, 1),
            'total_xp_earned': total_xp,
            'current_streak': student_profile.current_streak
        }