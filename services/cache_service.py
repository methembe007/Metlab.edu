"""
Centralized caching service for performance optimization
"""
import json
import hashlib
from typing import Any, Optional, Dict, List
from django.core.cache import caches
# from django.core.cache.utils import make_key  # Not needed for our implementation
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """Centralized service for managing application caching"""
    
    # Cache aliases
    DEFAULT_CACHE = 'default'
    AI_CACHE = 'ai_cache'
    ANALYTICS_CACHE = 'analytics'
    
    # Cache timeouts (in seconds)
    TIMEOUTS = {
        'user_profile': 900,        # 15 minutes
        'student_analytics': 1800,  # 30 minutes
        'leaderboard': 600,         # 10 minutes
        'achievements': 3600,       # 1 hour
        'content_summary': 86400,   # 24 hours
        'ai_generation': 86400,     # 24 hours
        'weakness_analysis': 1800,  # 30 minutes
        'recommendations': 900,     # 15 minutes
        'daily_lesson': 3600,       # 1 hour
        'shop_items': 3600,         # 1 hour
        'tutor_recommendations': 1800,  # 30 minutes
    }
    
    @classmethod
    def get_cache(cls, alias: str = DEFAULT_CACHE):
        """Get cache instance by alias"""
        return caches[alias]
    
    @classmethod
    def generate_key(cls, prefix: str, *args, **kwargs) -> str:
        """Generate a consistent cache key"""
        key_parts = [prefix]
        
        # Add positional arguments
        for arg in args:
            if isinstance(arg, (int, str)):
                key_parts.append(str(arg))
            else:
                key_parts.append(str(hash(str(arg))))
        
        # Add keyword arguments (sorted for consistency)
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        
        key = ":".join(key_parts)
        
        # Hash long keys to avoid Redis key length limits
        if len(key) > 200:
            key_hash = hashlib.md5(key.encode()).hexdigest()
            key = f"{prefix}:hash:{key_hash}"
        
        return key
    
    @classmethod
    def set(cls, key: str, value: Any, timeout: Optional[int] = None, 
            cache_alias: str = DEFAULT_CACHE) -> bool:
        """Set a value in cache"""
        try:
            cache = cls.get_cache(cache_alias)
            cache.set(key, value, timeout)
            return True
        except Exception as e:
            logger.error(f"Cache set failed for key {key}: {str(e)}")
            return False
    
    @classmethod
    def get(cls, key: str, default: Any = None, 
            cache_alias: str = DEFAULT_CACHE) -> Any:
        """Get a value from cache"""
        try:
            cache = cls.get_cache(cache_alias)
            return cache.get(key, default)
        except Exception as e:
            logger.error(f"Cache get failed for key {key}: {str(e)}")
            return default
    
    @classmethod
    def delete(cls, key: str, cache_alias: str = DEFAULT_CACHE) -> bool:
        """Delete a value from cache"""
        try:
            cache = cls.get_cache(cache_alias)
            cache.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete failed for key {key}: {str(e)}")
            return False
    
    @classmethod
    def delete_pattern(cls, pattern: str, cache_alias: str = DEFAULT_CACHE) -> bool:
        """Delete all keys matching a pattern"""
        try:
            cache = cls.get_cache(cache_alias)
            if hasattr(cache, 'delete_pattern'):
                cache.delete_pattern(pattern)
                return True
            else:
                logger.warning(f"Cache backend doesn't support pattern deletion")
                return False
        except Exception as e:
            logger.error(f"Cache pattern delete failed for pattern {pattern}: {str(e)}")
            return False
    
    @classmethod
    def get_or_set(cls, key: str, callable_func, timeout: Optional[int] = None,
                   cache_alias: str = DEFAULT_CACHE) -> Any:
        """Get value from cache or set it using the callable"""
        try:
            cache = cls.get_cache(cache_alias)
            return cache.get_or_set(key, callable_func, timeout)
        except Exception as e:
            logger.error(f"Cache get_or_set failed for key {key}: {str(e)}")
            # Fallback to calling the function directly
            return callable_func()


class StudentCacheService:
    """Specialized caching service for student-related data"""
    
    @classmethod
    def get_student_profile_key(cls, student_id: int) -> str:
        """Generate cache key for student profile"""
        return CacheService.generate_key('student_profile', student_id)
    
    @classmethod
    def cache_student_profile(cls, student_profile) -> bool:
        """Cache student profile data"""
        key = cls.get_student_profile_key(student_profile.id)
        profile_data = {
            'id': student_profile.id,
            'user_id': student_profile.user.id,
            'username': student_profile.user.username,
            'total_xp': student_profile.total_xp,
            'current_streak': student_profile.current_streak,
            'level': student_profile.level,
            'learning_preferences': student_profile.learning_preferences,
            'subjects_of_interest': student_profile.subjects_of_interest,
            'leaderboard_visible': student_profile.leaderboard_visible,
        }
        return CacheService.set(
            key, profile_data, 
            timeout=CacheService.TIMEOUTS['user_profile']
        )
    
    @classmethod
    def get_cached_student_profile(cls, student_id: int) -> Optional[Dict]:
        """Get cached student profile data"""
        key = cls.get_student_profile_key(student_id)
        return CacheService.get(key)
    
    @classmethod
    def invalidate_student_profile(cls, student_id: int) -> bool:
        """Invalidate cached student profile"""
        key = cls.get_student_profile_key(student_id)
        return CacheService.delete(key)
    
    @classmethod
    def get_student_analytics_key(cls, student_id: int, days: int = 30) -> str:
        """Generate cache key for student analytics"""
        return CacheService.generate_key('student_analytics', student_id, days)
    
    @classmethod
    def cache_student_analytics(cls, student_id: int, analytics_data: Dict, 
                               days: int = 30) -> bool:
        """Cache student analytics data"""
        key = cls.get_student_analytics_key(student_id, days)
        return CacheService.set(
            key, analytics_data,
            timeout=CacheService.TIMEOUTS['student_analytics'],
            cache_alias=CacheService.ANALYTICS_CACHE
        )
    
    @classmethod
    def get_cached_student_analytics(cls, student_id: int, 
                                   days: int = 30) -> Optional[Dict]:
        """Get cached student analytics data"""
        key = cls.get_student_analytics_key(student_id, days)
        return CacheService.get(key, cache_alias=CacheService.ANALYTICS_CACHE)


class LeaderboardCacheService:
    """Specialized caching service for leaderboard data"""
    
    @classmethod
    def get_leaderboard_key(cls, leaderboard_type: str, subject: str = '', 
                           limit: int = 10) -> str:
        """Generate cache key for leaderboard"""
        return CacheService.generate_key(
            'leaderboard', leaderboard_type, subject, limit
        )
    
    @classmethod
    def cache_leaderboard(cls, leaderboard_type: str, leaderboard_data: List,
                         subject: str = '', limit: int = 10) -> bool:
        """Cache leaderboard data"""
        key = cls.get_leaderboard_key(leaderboard_type, subject, limit)
        return CacheService.set(
            key, leaderboard_data,
            timeout=CacheService.TIMEOUTS['leaderboard']
        )
    
    @classmethod
    def get_cached_leaderboard(cls, leaderboard_type: str, subject: str = '',
                              limit: int = 10) -> Optional[List]:
        """Get cached leaderboard data"""
        key = cls.get_leaderboard_key(leaderboard_type, subject, limit)
        return CacheService.get(key)
    
    @classmethod
    def invalidate_leaderboards(cls) -> bool:
        """Invalidate all leaderboard caches"""
        return CacheService.delete_pattern('*leaderboard*')


class AICacheService:
    """Specialized caching service for AI-generated content"""
    
    @classmethod
    def get_ai_content_key(cls, content_id: int, generation_type: str) -> str:
        """Generate cache key for AI-generated content"""
        return CacheService.generate_key(
            'ai_content', content_id, generation_type
        )
    
    @classmethod
    def cache_ai_content(cls, content_id: int, generation_type: str, 
                        ai_data: Dict) -> bool:
        """Cache AI-generated content"""
        key = cls.get_ai_content_key(content_id, generation_type)
        return CacheService.set(
            key, ai_data,
            timeout=CacheService.TIMEOUTS['ai_generation'],
            cache_alias=CacheService.AI_CACHE
        )
    
    @classmethod
    def get_cached_ai_content(cls, content_id: int, 
                             generation_type: str) -> Optional[Dict]:
        """Get cached AI-generated content"""
        key = cls.get_ai_content_key(content_id, generation_type)
        return CacheService.get(key, cache_alias=CacheService.AI_CACHE)
    
    @classmethod
    def get_concept_extraction_key(cls, text_hash: str) -> str:
        """Generate cache key for concept extraction"""
        return CacheService.generate_key('concept_extraction', text_hash)
    
    @classmethod
    def cache_concept_extraction(cls, text: str, concepts: List[str]) -> bool:
        """Cache concept extraction results"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        key = cls.get_concept_extraction_key(text_hash)
        return CacheService.set(
            key, concepts,
            timeout=CacheService.TIMEOUTS['ai_generation'],
            cache_alias=CacheService.AI_CACHE
        )
    
    @classmethod
    def get_cached_concept_extraction(cls, text: str) -> Optional[List[str]]:
        """Get cached concept extraction results"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        key = cls.get_concept_extraction_key(text_hash)
        return CacheService.get(key, cache_alias=CacheService.AI_CACHE)


class WeaknessCacheService:
    """Specialized caching service for weakness analysis"""
    
    @classmethod
    def get_weakness_key(cls, student_id: int) -> str:
        """Generate cache key for student weaknesses"""
        return CacheService.generate_key('student_weaknesses', student_id)
    
    @classmethod
    def cache_student_weaknesses(cls, student_id: int, 
                                weaknesses_data: List[Dict]) -> bool:
        """Cache student weakness analysis"""
        key = cls.get_weakness_key(student_id)
        return CacheService.set(
            key, weaknesses_data,
            timeout=CacheService.TIMEOUTS['weakness_analysis'],
            cache_alias=CacheService.ANALYTICS_CACHE
        )
    
    @classmethod
    def get_cached_student_weaknesses(cls, student_id: int) -> Optional[List[Dict]]:
        """Get cached student weakness analysis"""
        key = cls.get_weakness_key(student_id)
        return CacheService.get(key, cache_alias=CacheService.ANALYTICS_CACHE)
    
    @classmethod
    def invalidate_student_weaknesses(cls, student_id: int) -> bool:
        """Invalidate cached student weaknesses"""
        key = cls.get_weakness_key(student_id)
        return CacheService.delete(key, cache_alias=CacheService.ANALYTICS_CACHE)


class RecommendationCacheService:
    """Specialized caching service for recommendations"""
    
    @classmethod
    def get_recommendations_key(cls, student_id: int) -> str:
        """Generate cache key for student recommendations"""
        return CacheService.generate_key('student_recommendations', student_id)
    
    @classmethod
    def cache_student_recommendations(cls, student_id: int, 
                                    recommendations: List[Dict]) -> bool:
        """Cache student recommendations"""
        key = cls.get_recommendations_key(student_id)
        return CacheService.set(
            key, recommendations,
            timeout=CacheService.TIMEOUTS['recommendations']
        )
    
    @classmethod
    def get_cached_student_recommendations(cls, student_id: int) -> Optional[List[Dict]]:
        """Get cached student recommendations"""
        key = cls.get_recommendations_key(student_id)
        return CacheService.get(key)
    
    @classmethod
    def invalidate_student_recommendations(cls, student_id: int) -> bool:
        """Invalidate cached student recommendations"""
        key = cls.get_recommendations_key(student_id)
        return CacheService.delete(key)


class DailyLessonCacheService:
    """Specialized caching service for daily lessons"""
    
    @classmethod
    def get_daily_lesson_key(cls, student_id: int, lesson_date: str) -> str:
        """Generate cache key for daily lesson"""
        return CacheService.generate_key('daily_lesson', student_id, lesson_date)
    
    @classmethod
    def cache_daily_lesson(cls, student_id: int, lesson_date: str, 
                          lesson_data: Dict) -> bool:
        """Cache daily lesson data"""
        key = cls.get_daily_lesson_key(student_id, lesson_date)
        return CacheService.set(
            key, lesson_data,
            timeout=CacheService.TIMEOUTS['daily_lesson']
        )
    
    @classmethod
    def get_cached_daily_lesson(cls, student_id: int, 
                               lesson_date: str) -> Optional[Dict]:
        """Get cached daily lesson data"""
        key = cls.get_daily_lesson_key(student_id, lesson_date)
        return CacheService.get(key)


class ShopCacheService:
    """Specialized caching service for shop items"""
    
    @classmethod
    def get_shop_items_key(cls, item_type: Optional[str] = None) -> str:
        """Generate cache key for shop items"""
        return CacheService.generate_key('shop_items', item_type or 'all')
    
    @classmethod
    def cache_shop_items(cls, items_data: List[Dict], 
                        item_type: Optional[str] = None) -> bool:
        """Cache shop items data"""
        key = cls.get_shop_items_key(item_type)
        return CacheService.set(
            key, items_data,
            timeout=CacheService.TIMEOUTS['shop_items']
        )
    
    @classmethod
    def get_cached_shop_items(cls, item_type: Optional[str] = None) -> Optional[List[Dict]]:
        """Get cached shop items data"""
        key = cls.get_shop_items_key(item_type)
        return CacheService.get(key)
    
    @classmethod
    def invalidate_shop_items(cls) -> bool:
        """Invalidate all shop items cache"""
        return CacheService.delete_pattern('*shop_items*')


class CacheInvalidationService:
    """Service for managing cache invalidation"""
    
    @classmethod
    def invalidate_student_caches(cls, student_id: int) -> None:
        """Invalidate all caches related to a student"""
        StudentCacheService.invalidate_student_profile(student_id)
        WeaknessCacheService.invalidate_student_weaknesses(student_id)
        RecommendationCacheService.invalidate_student_recommendations(student_id)
        
        # Invalidate analytics cache
        pattern = f"*student_analytics:{student_id}*"
        CacheService.delete_pattern(pattern, CacheService.ANALYTICS_CACHE)
    
    @classmethod
    def invalidate_leaderboard_caches(cls) -> None:
        """Invalidate all leaderboard caches"""
        LeaderboardCacheService.invalidate_leaderboards()
    
    @classmethod
    def invalidate_content_caches(cls, content_id: int) -> None:
        """Invalidate all caches related to content"""
        # Invalidate AI-generated content caches
        pattern = f"*ai_content:{content_id}*"
        CacheService.delete_pattern(pattern, CacheService.AI_CACHE)
    
    @classmethod
    def invalidate_all_caches(cls) -> None:
        """Invalidate all application caches (use with caution)"""
        for cache_alias in ['default', 'ai_cache', 'analytics']:
            try:
                cache = CacheService.get_cache(cache_alias)
                cache.clear()
            except Exception as e:
                logger.error(f"Failed to clear cache {cache_alias}: {str(e)}")


# Decorator for caching function results
def cache_result(timeout: int = 300, cache_alias: str = CacheService.DEFAULT_CACHE,
                key_prefix: str = 'func_cache'):
    """Decorator to cache function results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key based on function name and arguments
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            
            cache_key = CacheService.generate_key(*key_parts)
            
            # Try to get from cache first
            result = CacheService.get(cache_key, cache_alias=cache_alias)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            CacheService.set(cache_key, result, timeout, cache_alias)
            return result
        
        return wrapper
    return decorator