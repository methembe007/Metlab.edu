"""
Database query optimization service for performance monitoring and optimization
"""
import time
import logging
from typing import Dict, List, Any, Optional
from django.db import connection
from django.db.models import QuerySet, Prefetch
from django.core.cache import cache
from django.conf import settings
from contextlib import contextmanager
from functools import wraps

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Service for optimizing database queries and monitoring performance"""
    
    # Query performance thresholds (in seconds)
    SLOW_QUERY_THRESHOLD = 0.5
    VERY_SLOW_QUERY_THRESHOLD = 2.0
    
    @classmethod
    def optimize_learning_session_queries(cls, student_profile):
        """Optimize common learning session queries"""
        from learning.models import LearningSession
        
        # Use select_related for foreign keys and prefetch_related for many-to-many
        return LearningSession.objects.select_related(
            'student__user',
            'content'
        ).filter(
            student=student_profile
        ).order_by('-start_time')
    
    @classmethod
    def optimize_student_analytics_query(cls, student_profile, days=30):
        """Optimize student analytics query with proper joins"""
        from learning.models import LearningSession
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        return LearningSession.objects.select_related(
            'content'
        ).filter(
            student=student_profile,
            start_time__gte=cutoff_date,
            status='completed'
        ).only(
            'id', 'start_time', 'end_time', 'performance_score',
            'time_spent_minutes', 'questions_attempted', 'questions_correct',
            'concepts_covered', 'difficulty_level', 'content__subject'
        )
    
    @classmethod
    def optimize_weakness_analysis_query(cls, student_profile):
        """Optimize weakness analysis query"""
        from learning.models import WeaknessAnalysis
        
        return WeaknessAnalysis.objects.filter(
            student=student_profile
        ).order_by('-priority_level', '-weakness_score').only(
            'id', 'subject', 'concept', 'weakness_score', 'weakness_level',
            'total_attempts', 'correct_attempts', 'priority_level',
            'improvement_trend', 'last_updated'
        )
    
    @classmethod
    def optimize_leaderboard_query(cls, leaderboard_type='weekly', subject='', limit=10):
        """Optimize leaderboard query with proper indexing"""
        from gamification.models import Leaderboard
        
        queryset = Leaderboard.objects.select_related(
            'student__user'
        ).filter(
            leaderboard_type=leaderboard_type,
            subject=subject,
            student__leaderboard_visible=True
        ).only(
            'rank', 'weekly_xp', 'monthly_xp', 'all_time_xp',
            'student__user__username', 'student__user__first_name',
            'student__user__last_name', 'student__show_real_name'
        ).order_by('rank')[:limit]
        
        return queryset
    
    @classmethod
    def optimize_daily_lesson_query(cls, student_profile, lesson_date):
        """Optimize daily lesson query"""
        from learning.models import DailyLesson
        
        return DailyLesson.objects.select_related(
            'student__user'
        ).prefetch_related(
            'related_content',
            'related_weaknesses'
        ).filter(
            student=student_profile,
            lesson_date=lesson_date
        ).first()
    
    @classmethod
    def optimize_content_library_query(cls, user):
        """Optimize content library query"""
        from content.models import UploadedContent
        
        return UploadedContent.objects.select_related(
            'user'
        ).prefetch_related(
            Prefetch('summaries'),
            Prefetch('quizzes'),
            Prefetch('flashcards')
        ).filter(
            user=user,
            processing_status='completed'
        ).only(
            'id', 'original_filename', 'content_type', 'subject',
            'difficulty_level', 'created_at', 'file_size',
            'key_concepts', 'user__username'
        ).order_by('-created_at')
    
    @classmethod
    def optimize_tutor_recommendations_query(cls, student_profile):
        """Optimize tutor recommendations query"""
        from community.models import TutorProfile, Subject
        
        # Get student's subjects of interest
        student_subjects = student_profile.subjects_of_interest
        
        if not student_subjects:
            # If no subjects specified, get all active tutors
            return TutorProfile.objects.select_related(
                'user'
            ).prefetch_related(
                'subjects'
            ).filter(
                status='active',
                verified=True
            ).order_by('-rating', '-total_sessions')[:20]
        
        # Filter tutors by subjects
        return TutorProfile.objects.select_related(
            'user'
        ).prefetch_related(
            'subjects'
        ).filter(
            status='active',
            verified=True,
            subjects__name__in=student_subjects
        ).distinct().order_by('-rating', '-total_sessions')[:20]
    
    @classmethod
    def optimize_study_group_query(cls, student_profile):
        """Optimize study group query"""
        from community.models import StudyGroup
        
        return StudyGroup.objects.select_related(
            'subject',
            'created_by__user'
        ).prefetch_related(
            Prefetch(
                'memberships',
                queryset=cls._get_active_memberships_queryset()
            )
        ).filter(
            status='active',
            is_public=True
        ).annotate(
            member_count=cls._get_member_count_annotation()
        ).order_by('-created_at')
    
    @classmethod
    def _get_active_memberships_queryset(cls):
        """Get optimized queryset for active memberships"""
        from community.models import StudyGroupMembership
        
        return StudyGroupMembership.objects.select_related(
            'student__user'
        ).filter(status='active').only(
            'student__user__username', 'role', 'joined_at'
        )
    
    @classmethod
    def _get_member_count_annotation(cls):
        """Get annotation for member count"""
        from django.db.models import Count, Q
        
        return Count(
            'memberships',
            filter=Q(memberships__status='active')
        )


class QueryMonitor:
    """Monitor and log database query performance"""
    
    def __init__(self):
        self.query_log = []
        self.slow_queries = []
    
    @contextmanager
    def monitor_queries(self, operation_name: str = "database_operation"):
        """Context manager to monitor queries in a block of code"""
        initial_queries = len(connection.queries)
        start_time = time.time()
        
        try:
            yield self
        finally:
            end_time = time.time()
            duration = end_time - start_time
            
            new_queries = connection.queries[initial_queries:]
            query_count = len(new_queries)
            
            # Log performance metrics
            self._log_query_performance(
                operation_name, query_count, duration, new_queries
            )
    
    def _log_query_performance(self, operation_name: str, query_count: int,
                              duration: float, queries: List[Dict]):
        """Log query performance metrics"""
        if duration > QueryOptimizer.SLOW_QUERY_THRESHOLD:
            logger.warning(
                f"Slow operation '{operation_name}': {query_count} queries "
                f"in {duration:.3f}s"
            )
            
            # Log individual slow queries
            for query in queries:
                query_time = float(query.get('time', 0))
                if query_time > QueryOptimizer.SLOW_QUERY_THRESHOLD:
                    logger.warning(
                        f"Slow query ({query_time:.3f}s): {query['sql'][:200]}..."
                    )
                    self.slow_queries.append({
                        'sql': query['sql'],
                        'time': query_time,
                        'operation': operation_name
                    })
        else:
            logger.info(
                f"Operation '{operation_name}': {query_count} queries "
                f"in {duration:.3f}s"
            )
    
    def get_slow_queries(self) -> List[Dict]:
        """Get list of slow queries"""
        return self.slow_queries
    
    def reset_monitoring(self):
        """Reset monitoring data"""
        self.query_log = []
        self.slow_queries = []


def monitor_queries(operation_name: str = "database_operation"):
    """Decorator to monitor queries in a function"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            monitor = QueryMonitor()
            with monitor.monitor_queries(operation_name):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator


class BulkOperationOptimizer:
    """Optimize bulk database operations"""
    
    @classmethod
    def bulk_update_leaderboards(cls, leaderboard_entries: List):
        """Efficiently update multiple leaderboard entries"""
        from gamification.models import Leaderboard
        
        if not leaderboard_entries:
            return
        
        # Use bulk_update for better performance
        Leaderboard.objects.bulk_update(
            leaderboard_entries,
            ['weekly_xp', 'monthly_xp', 'all_time_xp', 'rank'],
            batch_size=100
        )
    
    @classmethod
    def bulk_create_xp_transactions(cls, transactions: List):
        """Efficiently create multiple XP transactions"""
        from gamification.models import XPTransaction
        
        if not transactions:
            return
        
        XPTransaction.objects.bulk_create(
            transactions,
            batch_size=100,
            ignore_conflicts=True
        )
    
    @classmethod
    def bulk_update_weakness_analysis(cls, weakness_entries: List):
        """Efficiently update multiple weakness analysis entries"""
        from learning.models import WeaknessAnalysis
        
        if not weakness_entries:
            return
        
        WeaknessAnalysis.objects.bulk_update(
            weakness_entries,
            ['weakness_score', 'total_attempts', 'correct_attempts',
             'last_attempt_score', 'improvement_trend', 'priority_level'],
            batch_size=50
        )


class DatabaseHealthMonitor:
    """Monitor database health and performance"""
    
    @classmethod
    def check_database_performance(cls) -> Dict[str, Any]:
        """Check overall database performance metrics"""
        with connection.cursor() as cursor:
            # Get database size (SQLite specific)
            cursor.execute("PRAGMA page_count;")
            page_count = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA page_size;")
            page_size = cursor.fetchone()[0]
            
            db_size_mb = (page_count * page_size) / (1024 * 1024)
            
            # Get table statistics
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name;
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            table_stats = {}
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                row_count = cursor.fetchone()[0]
                table_stats[table] = row_count
        
        return {
            'database_size_mb': round(db_size_mb, 2),
            'table_statistics': table_stats,
            'total_tables': len(tables)
        }
    
    @classmethod
    def analyze_query_patterns(cls) -> Dict[str, Any]:
        """Analyze common query patterns for optimization opportunities"""
        # This would be more sophisticated in a production environment
        # with query log analysis
        return {
            'recommendations': [
                'Consider adding indexes for frequently queried columns',
                'Use select_related() for foreign key relationships',
                'Use prefetch_related() for many-to-many relationships',
                'Implement caching for expensive queries',
                'Use bulk operations for multiple database writes'
            ]
        }
    
    @classmethod
    def get_index_usage_stats(cls) -> Dict[str, Any]:
        """Get statistics about index usage (SQLite specific)"""
        with connection.cursor() as cursor:
            # Get index information
            cursor.execute("""
                SELECT name, tbl_name, sql 
                FROM sqlite_master 
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
                ORDER BY tbl_name, name;
            """)
            
            indexes = []
            for row in cursor.fetchall():
                indexes.append({
                    'name': row[0],
                    'table': row[1],
                    'definition': row[2]
                })
        
        return {
            'total_indexes': len(indexes),
            'indexes': indexes
        }


# Global query monitor instance
query_monitor = QueryMonitor()