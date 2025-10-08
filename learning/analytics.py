"""
Advanced analytics engine for learning performance analysis and adaptive learning
"""
import math
from datetime import timedelta, datetime
from django.utils import timezone
from django.db.models import Avg, Count, Sum, Q, F
from django.db.models.functions import TruncDate, TruncWeek
from collections import defaultdict, Counter

from .models import LearningSession, WeaknessAnalysis, PersonalizedRecommendation
from accounts.models import StudentProfile
from content.models import UploadedContent


class PerformanceAnalyticsEngine:
    """Advanced analytics engine for processing learning performance data"""
    
    @staticmethod
    def analyze_learning_patterns(student_profile, days=30):
        """Analyze learning patterns and identify trends"""
        cutoff_date = timezone.now() - timedelta(days=days)
        
        sessions = LearningSession.objects.filter(
            student=student_profile,
            start_time__gte=cutoff_date,
            status='completed'
        ).order_by('start_time')
        
        if not sessions.exists():
            return {
                'total_sessions': 0,
                'learning_velocity': 0,
                'consistency_score': 0,
                'improvement_trend': 'unknown',
                'peak_performance_time': None,
                'preferred_session_length': 0,
                'subject_distribution': {},
                'difficulty_progression': 'stable'
            }
        
        # Calculate learning velocity (sessions per week)
        weeks = max(1, days // 7)
        learning_velocity = sessions.count() / weeks
        
        # Calculate consistency score (how regularly the student studies)
        session_dates = sessions.values_list('start_time__date', flat=True)
        unique_days = len(set(session_dates))
        consistency_score = (unique_days / days) * 100
        
        # Analyze improvement trend
        improvement_trend = PerformanceAnalyticsEngine._calculate_improvement_trend(sessions)
        
        # Find peak performance time
        peak_performance_time = PerformanceAnalyticsEngine._find_peak_performance_time(sessions)
        
        # Calculate preferred session length
        avg_session_length = sessions.aggregate(avg_length=Avg('time_spent_minutes'))['avg_length'] or 0
        
        # Subject distribution
        subject_distribution = PerformanceAnalyticsEngine._analyze_subject_distribution(sessions)
        
        # Difficulty progression
        difficulty_progression = PerformanceAnalyticsEngine._analyze_difficulty_progression(sessions)
        
        return {
            'total_sessions': sessions.count(),
            'learning_velocity': round(learning_velocity, 2),
            'consistency_score': round(consistency_score, 2),
            'improvement_trend': improvement_trend,
            'peak_performance_time': peak_performance_time,
            'preferred_session_length': round(avg_session_length, 1),
            'subject_distribution': subject_distribution,
            'difficulty_progression': difficulty_progression
        }
    
    @staticmethod
    def _calculate_improvement_trend(sessions):
        """Calculate if student performance is improving, stable, or declining"""
        if sessions.count() < 3:
            return 'insufficient_data'
        
        # Split sessions into first half and second half
        session_list = list(sessions)
        mid_point = len(session_list) // 2
        
        first_half_avg = sum(s.performance_score or 0 for s in session_list[:mid_point]) / mid_point
        second_half_avg = sum(s.performance_score or 0 for s in session_list[mid_point:]) / (len(session_list) - mid_point)
        
        improvement = second_half_avg - first_half_avg
        
        if improvement > 5:
            return 'improving'
        elif improvement < -5:
            return 'declining'
        else:
            return 'stable'
    
    @staticmethod
    def _find_peak_performance_time(sessions):
        """Find the time of day when student performs best"""
        hour_performance = defaultdict(list)
        
        for session in sessions:
            if session.performance_score:
                hour = session.start_time.hour
                hour_performance[hour].append(session.performance_score)
        
        if not hour_performance:
            return None
        
        # Calculate average performance for each hour
        hour_averages = {
            hour: sum(scores) / len(scores)
            for hour, scores in hour_performance.items()
        }
        
        best_hour = max(hour_averages, key=hour_averages.get)
        return f"{best_hour:02d}:00"
    
    @staticmethod
    def _analyze_subject_distribution(sessions):
        """Analyze distribution of study time across subjects"""
        subject_time = defaultdict(int)
        
        for session in sessions:
            subject = session.content.subject or 'General'
            subject_time[subject] += session.time_spent_minutes
        
        total_time = sum(subject_time.values())
        if total_time == 0:
            return {}
        
        return {
            subject: round((time / total_time) * 100, 1)
            for subject, time in subject_time.items()
        }
    
    @staticmethod
    def _analyze_difficulty_progression(sessions):
        """Analyze how student handles different difficulty levels over time"""
        if sessions.count() < 5:
            return 'insufficient_data'
        
        # Group sessions by difficulty and calculate average performance
        difficulty_performance = sessions.values('difficulty_level').annotate(
            avg_performance=Avg('performance_score'),
            session_count=Count('id')
        ).filter(session_count__gte=2)  # Only consider difficulties with at least 2 sessions
        
        if not difficulty_performance:
            return 'stable'
        
        # Check if student is consistently performing well on harder content
        performance_by_difficulty = {item['difficulty_level']: item['avg_performance'] for item in difficulty_performance}
        
        if 'advanced' in performance_by_difficulty and performance_by_difficulty['advanced'] > 70:
            return 'advancing'
        elif 'beginner' in performance_by_difficulty and performance_by_difficulty['beginner'] < 60:
            return 'struggling'
        else:
            return 'stable'


class WeaknessIdentificationEngine:
    """Engine for identifying and analyzing student weaknesses"""
    
    @staticmethod
    def identify_weaknesses(student_profile, threshold=60.0):
        """Identify concepts where student shows weakness"""
        # Get all learning sessions for the student
        sessions = LearningSession.objects.filter(
            student=student_profile,
            status='completed'
        )
        
        concept_performance = defaultdict(lambda: {'attempts': 0, 'correct': 0, 'scores': []})
        
        # Aggregate performance data by concept
        for session in sessions:
            if session.concepts_covered and session.performance_score is not None:
                concepts_in_session = len(session.concepts_covered)
                if concepts_in_session > 0:
                    # Distribute questions across concepts
                    questions_per_concept = session.questions_attempted / concepts_in_session
                    correct_per_concept = (session.questions_correct / session.questions_attempted) * questions_per_concept if session.questions_attempted > 0 else 0
                    
                    for concept in session.concepts_covered:
                        concept_performance[concept]['attempts'] += questions_per_concept
                        concept_performance[concept]['correct'] += correct_per_concept
                        concept_performance[concept]['scores'].append(session.performance_score)
        
        # Identify weaknesses
        weaknesses = []
        for concept, data in concept_performance.items():
            if data['attempts'] >= 3:  # Only consider concepts with sufficient data
                accuracy = (data['correct'] / data['attempts']) * 100 if data['attempts'] > 0 else 0
                avg_score = sum(data['scores']) / len(data['scores']) if data['scores'] else 0
                
                # Consider it a weakness if accuracy or average score is below threshold
                if accuracy < threshold or avg_score < threshold:
                    weakness_score = 100 - min(accuracy, avg_score)
                    weaknesses.append({
                        'concept': concept,
                        'weakness_score': weakness_score,
                        'accuracy': accuracy,
                        'avg_score': avg_score,
                        'total_attempts': data['attempts'],
                        'improvement_potential': WeaknessIdentificationEngine._calculate_improvement_potential(data['scores'])
                    })
        
        # Sort by weakness score (highest first)
        weaknesses.sort(key=lambda x: x['weakness_score'], reverse=True)
        return weaknesses
    
    @staticmethod
    def _calculate_improvement_potential(scores):
        """Calculate potential for improvement based on score variance"""
        if len(scores) < 3:
            return 'unknown'
        
        # Calculate trend in recent scores
        recent_scores = scores[-3:]
        if len(recent_scores) >= 2:
            trend = recent_scores[-1] - recent_scores[0]
            if trend > 10:
                return 'high'  # Already improving
            elif trend < -10:
                return 'critical'  # Getting worse
        
        # Calculate variance
        avg_score = sum(scores) / len(scores)
        variance = sum((score - avg_score) ** 2 for score in scores) / len(scores)
        
        if variance > 400:  # High variance suggests inconsistent understanding
            return 'high'
        elif variance < 100:  # Low variance suggests consistent (but poor) performance
            return 'medium'
        else:
            return 'medium'
    
    @staticmethod
    def update_weakness_analysis(student_profile):
        """Update weakness analysis for a student based on recent performance"""
        weaknesses = WeaknessIdentificationEngine.identify_weaknesses(student_profile)
        
        # Update or create WeaknessAnalysis records
        for weakness_data in weaknesses:
            concept = weakness_data['concept']
            
            # Try to determine subject from recent sessions
            recent_sessions = LearningSession.objects.filter(
                student=student_profile,
                concepts_covered__contains=[concept]
            ).order_by('-start_time')[:5]
            
            subject = 'General'
            if recent_sessions.exists():
                subject = recent_sessions.first().content.subject or 'General'
            
            weakness, created = WeaknessAnalysis.objects.get_or_create(
                student=student_profile,
                subject=subject,
                concept=concept,
                defaults={
                    'weakness_score': weakness_data['weakness_score'],
                    'total_attempts': int(weakness_data['total_attempts']),
                    'correct_attempts': int(weakness_data['total_attempts'] * weakness_data['accuracy'] / 100),
                    'last_attempt_score': weakness_data['avg_score']
                }
            )
            
            if not created:
                # Update existing record
                weakness.weakness_score = weakness_data['weakness_score']
                weakness.total_attempts = int(weakness_data['total_attempts'])
                weakness.correct_attempts = int(weakness_data['total_attempts'] * weakness_data['accuracy'] / 100)
                weakness.last_attempt_score = weakness_data['avg_score']
            
            weakness.calculate_weakness_score()
            weakness.save()


class AdaptiveDifficultyEngine:
    """Engine for adaptive difficulty adjustment based on performance"""
    
    @staticmethod
    def recommend_difficulty(student_profile, content_subject=None):
        """Recommend difficulty level for new content based on student performance"""
        # Get recent performance in the subject
        sessions_filter = Q(student=student_profile, status='completed')
        if content_subject:
            sessions_filter &= Q(content__subject=content_subject)
        
        recent_sessions = LearningSession.objects.filter(sessions_filter).order_by('-start_time')[:10]
        
        if not recent_sessions.exists():
            return 'intermediate'  # Default for new students
        
        # Calculate average performance and consistency
        avg_performance = recent_sessions.aggregate(avg=Avg('performance_score'))['avg'] or 0
        performance_scores = [s.performance_score for s in recent_sessions if s.performance_score is not None]
        
        if not performance_scores:
            return 'intermediate'
        
        # Calculate performance variance
        variance = sum((score - avg_performance) ** 2 for score in performance_scores) / len(performance_scores)
        consistency = 100 - min(100, variance / 4)  # Convert variance to consistency score
        
        # Recommend difficulty based on performance and consistency
        if avg_performance >= 85 and consistency >= 70:
            return 'advanced'
        elif avg_performance >= 70 and consistency >= 60:
            return 'intermediate'
        elif avg_performance < 50 or consistency < 40:
            return 'beginner'
        else:
            return 'intermediate'
    
    @staticmethod
    def adjust_session_difficulty(session_id, performance_feedback):
        """Dynamically adjust difficulty during a session based on performance"""
        try:
            session = LearningSession.objects.get(id=session_id, status='active')
            current_performance = performance_feedback.get('current_accuracy', 0)
            questions_answered = performance_feedback.get('questions_answered', 0)
            
            if questions_answered < 3:
                return session.difficulty_level  # Not enough data yet
            
            # Adjust difficulty based on current performance
            if current_performance >= 90:
                # Student is doing very well, increase difficulty
                if session.difficulty_level == 'beginner':
                    new_difficulty = 'intermediate'
                elif session.difficulty_level == 'intermediate':
                    new_difficulty = 'advanced'
                else:
                    new_difficulty = 'advanced'
            elif current_performance <= 40:
                # Student is struggling, decrease difficulty
                if session.difficulty_level == 'advanced':
                    new_difficulty = 'intermediate'
                elif session.difficulty_level == 'intermediate':
                    new_difficulty = 'beginner'
                else:
                    new_difficulty = 'beginner'
            else:
                # Performance is acceptable, maintain current difficulty
                new_difficulty = session.difficulty_level
            
            if new_difficulty != session.difficulty_level:
                session.difficulty_level = new_difficulty
                session.save()
            
            return new_difficulty
            
        except LearningSession.DoesNotExist:
            return 'intermediate'


class RecommendationEngine:
    """Advanced recommendation engine for personalized learning suggestions"""
    
    @staticmethod
    def generate_comprehensive_recommendations(student_profile):
        """Generate comprehensive set of recommendations for a student"""
        recommendations = []
        
        # Get learning patterns
        patterns = PerformanceAnalyticsEngine.analyze_learning_patterns(student_profile)
        
        # Generate different types of recommendations
        recommendations.extend(RecommendationEngine._generate_weakness_recommendations(student_profile))
        recommendations.extend(RecommendationEngine._generate_consistency_recommendations(student_profile, patterns))
        recommendations.extend(RecommendationEngine._generate_difficulty_recommendations(student_profile))
        recommendations.extend(RecommendationEngine._generate_content_recommendations(student_profile))
        recommendations.extend(RecommendationEngine._generate_study_schedule_recommendations(student_profile, patterns))
        
        # Sort by priority and limit to top recommendations
        recommendations.sort(key=lambda x: x['priority'], reverse=True)
        return recommendations[:10]
    
    @staticmethod
    def _generate_weakness_recommendations(student_profile):
        """Generate recommendations based on identified weaknesses"""
        weaknesses = WeaknessIdentificationEngine.identify_weaknesses(student_profile)
        recommendations = []
        
        for weakness in weaknesses[:3]:  # Top 3 weaknesses
            priority = 5 if weakness['weakness_score'] > 80 else 4 if weakness['weakness_score'] > 60 else 3
            
            recommendations.append({
                'type': 'practice',
                'title': f"Practice {weakness['concept']}",
                'description': f"Focus on {weakness['concept']} - you've shown {weakness['weakness_score']:.1f}% weakness in this area.",
                'priority': priority,
                'estimated_time': 15 + (priority * 5),
                'content': {
                    'concept': weakness['concept'],
                    'weakness_score': weakness['weakness_score'],
                    'improvement_potential': weakness['improvement_potential']
                }
            })
        
        return recommendations
    
    @staticmethod
    def _generate_consistency_recommendations(student_profile, patterns):
        """Generate recommendations to improve study consistency"""
        recommendations = []
        
        if patterns['consistency_score'] < 30:
            recommendations.append({
                'type': 'study_plan',
                'title': 'Improve Study Consistency',
                'description': f"Your consistency score is {patterns['consistency_score']:.1f}%. Try studying for just 10 minutes daily to build a habit.",
                'priority': 4,
                'estimated_time': 10,
                'content': {
                    'current_consistency': patterns['consistency_score'],
                    'target_consistency': 70,
                    'suggested_daily_time': 10
                }
            })
        
        if patterns['learning_velocity'] < 1:
            recommendations.append({
                'type': 'study_plan',
                'title': 'Increase Learning Frequency',
                'description': f"You're studying {patterns['learning_velocity']:.1f} times per week. Try to increase to 3-4 sessions weekly.",
                'priority': 3,
                'estimated_time': 20,
                'content': {
                    'current_velocity': patterns['learning_velocity'],
                    'target_velocity': 3.5
                }
            })
        
        return recommendations
    
    @staticmethod
    def _generate_difficulty_recommendations(student_profile):
        """Generate recommendations for difficulty adjustment"""
        recommendations = []
        
        # Check recent performance across difficulty levels
        recent_sessions = LearningSession.objects.filter(
            student=student_profile,
            status='completed'
        ).order_by('-start_time')[:20]
        
        difficulty_performance = {}
        for session in recent_sessions:
            if session.performance_score is not None:
                if session.difficulty_level not in difficulty_performance:
                    difficulty_performance[session.difficulty_level] = []
                difficulty_performance[session.difficulty_level].append(session.performance_score)
        
        # Check if student is ready for harder content
        if 'intermediate' in difficulty_performance:
            avg_intermediate = sum(difficulty_performance['intermediate']) / len(difficulty_performance['intermediate'])
            if avg_intermediate > 85 and len(difficulty_performance['intermediate']) >= 3:
                if 'advanced' not in difficulty_performance or len(difficulty_performance['advanced']) < 2:
                    recommendations.append({
                        'type': 'difficulty',
                        'title': 'Try Advanced Content',
                        'description': f"You're excelling at intermediate level ({avg_intermediate:.1f}% average). Ready for a challenge?",
                        'priority': 3,
                        'estimated_time': 25,
                        'content': {
                            'current_level': 'intermediate',
                            'suggested_level': 'advanced',
                            'current_performance': avg_intermediate
                        }
                    })
        
        return recommendations
    
    @staticmethod
    def _generate_content_recommendations(student_profile):
        """Generate recommendations for new content to study"""
        recommendations = []
        
        # Find subjects the student has been studying
        studied_subjects = LearningSession.objects.filter(
            student=student_profile
        ).values_list('content__subject', flat=True).distinct()
        
        for subject in studied_subjects:
            if not subject:
                continue
                
            # Find unstudied content in this subject
            unstudied_content = UploadedContent.objects.filter(
                subject=subject,
                processing_status='completed'
            ).exclude(
                learning_sessions__student=student_profile
            ).first()
            
            if unstudied_content:
                recommendations.append({
                    'type': 'content',
                    'title': f'New {subject} Material',
                    'description': f'Explore new content: {unstudied_content.original_filename[:50]}...',
                    'priority': 2,
                    'estimated_time': 20,
                    'content': {
                        'content_id': unstudied_content.id,
                        'subject': subject,
                        'filename': unstudied_content.original_filename
                    }
                })
        
        return recommendations
    
    @staticmethod
    def _generate_study_schedule_recommendations(student_profile, patterns):
        """Generate recommendations for optimal study scheduling"""
        recommendations = []
        
        if patterns['peak_performance_time']:
            recommendations.append({
                'type': 'study_plan',
                'title': 'Optimize Study Time',
                'description': f"You perform best around {patterns['peak_performance_time']}. Schedule important sessions then!",
                'priority': 2,
                'estimated_time': 0,  # This is advice, not a task
                'content': {
                    'peak_time': patterns['peak_performance_time'],
                    'preferred_length': patterns['preferred_session_length']
                }
            })
        
        if patterns['preferred_session_length'] > 45:
            recommendations.append({
                'type': 'study_plan',
                'title': 'Break Up Long Sessions',
                'description': f"Your average session is {patterns['preferred_session_length']:.1f} minutes. Try shorter, focused sessions for better retention.",
                'priority': 2,
                'estimated_time': 25,
                'content': {
                    'current_length': patterns['preferred_session_length'],
                    'suggested_length': 25
                }
            })
        
        return recommendations