"""
Rate limiting and abuse prevention for video chat sessions.
Implements throttling for session creation and WebSocket messages.
Requirements: 1.2, 2.3
"""
import logging
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


class VideoSessionRateLimiter:
    """
    Rate limiter for video session operations.
    Uses Django cache to track request counts per user.
    """
    
    # Rate limit configurations
    SESSION_CREATION_LIMIT = 10  # Max sessions per hour
    SESSION_CREATION_WINDOW = 3600  # 1 hour in seconds
    
    WEBSOCKET_MESSAGE_LIMIT = 100  # Max messages per minute
    WEBSOCKET_MESSAGE_WINDOW = 60  # 1 minute in seconds
    
    JOIN_ATTEMPT_LIMIT = 5  # Max join attempts per session per user
    JOIN_ATTEMPT_WINDOW = 300  # 5 minutes in seconds
    
    @staticmethod
    def check_session_creation_limit(user):
        """
        Check if user has exceeded session creation rate limit.
        
        Args:
            user: User object attempting to create a session
            
        Returns:
            tuple: (is_allowed: bool, remaining: int, reset_time: datetime or None)
        """
        cache_key = f'session_creation_limit:{user.id}'
        
        # Get current count from cache
        current_count = cache.get(cache_key, 0)
        
        if current_count >= VideoSessionRateLimiter.SESSION_CREATION_LIMIT:
            # Get TTL to know when limit resets
            ttl = cache.ttl(cache_key)
            reset_time = timezone.now() + timedelta(seconds=ttl) if ttl else None
            
            logger.warning(
                f"Session creation rate limit exceeded for user {user.username}. "
                f"Count: {current_count}/{VideoSessionRateLimiter.SESSION_CREATION_LIMIT}"
            )
            return False, 0, reset_time
        
        # Increment counter
        if current_count == 0:
            # First request in window, set with expiry
            cache.set(
                cache_key,
                1,
                VideoSessionRateLimiter.SESSION_CREATION_WINDOW
            )
        else:
            # Increment existing counter
            cache.incr(cache_key)
        
        remaining = VideoSessionRateLimiter.SESSION_CREATION_LIMIT - (current_count + 1)
        return True, remaining, None
    
    @staticmethod
    def check_websocket_message_limit(user, session_id):
        """
        Check if user has exceeded WebSocket message rate limit for a session.
        
        Args:
            user: User object sending messages
            session_id: UUID of the session
            
        Returns:
            tuple: (is_allowed: bool, remaining: int, reset_time: datetime or None)
        """
        cache_key = f'ws_message_limit:{user.id}:{session_id}'
        
        # Get current count from cache
        current_count = cache.get(cache_key, 0)
        
        if current_count >= VideoSessionRateLimiter.WEBSOCKET_MESSAGE_LIMIT:
            # Get TTL to know when limit resets
            ttl = cache.ttl(cache_key)
            reset_time = timezone.now() + timedelta(seconds=ttl) if ttl else None
            
            logger.warning(
                f"WebSocket message rate limit exceeded for user {user.username} in session {session_id}. "
                f"Count: {current_count}/{VideoSessionRateLimiter.WEBSOCKET_MESSAGE_LIMIT}"
            )
            return False, 0, reset_time
        
        # Increment counter
        if current_count == 0:
            # First message in window, set with expiry
            cache.set(
                cache_key,
                1,
                VideoSessionRateLimiter.WEBSOCKET_MESSAGE_WINDOW
            )
        else:
            # Increment existing counter
            cache.incr(cache_key)
        
        remaining = VideoSessionRateLimiter.WEBSOCKET_MESSAGE_LIMIT - (current_count + 1)
        return True, remaining, None
    
    @staticmethod
    def check_join_attempt_limit(user, session_id):
        """
        Check if user has exceeded join attempt rate limit for a session.
        Prevents rapid join/leave spam.
        
        Args:
            user: User object attempting to join
            session_id: UUID of the session
            
        Returns:
            tuple: (is_allowed: bool, remaining: int, reset_time: datetime or None)
        """
        cache_key = f'join_attempt_limit:{user.id}:{session_id}'
        
        # Get current count from cache
        current_count = cache.get(cache_key, 0)
        
        if current_count >= VideoSessionRateLimiter.JOIN_ATTEMPT_LIMIT:
            # Get TTL to know when limit resets
            ttl = cache.ttl(cache_key)
            reset_time = timezone.now() + timedelta(seconds=ttl) if ttl else None
            
            logger.warning(
                f"Join attempt rate limit exceeded for user {user.username} in session {session_id}. "
                f"Count: {current_count}/{VideoSessionRateLimiter.JOIN_ATTEMPT_LIMIT}"
            )
            return False, 0, reset_time
        
        # Increment counter
        if current_count == 0:
            # First attempt in window, set with expiry
            cache.set(
                cache_key,
                1,
                VideoSessionRateLimiter.JOIN_ATTEMPT_WINDOW
            )
        else:
            # Increment existing counter
            cache.incr(cache_key)
        
        remaining = VideoSessionRateLimiter.JOIN_ATTEMPT_LIMIT - (current_count + 1)
        return True, remaining, None
    
    @staticmethod
    def reset_user_limits(user):
        """
        Reset all rate limits for a user.
        Useful for administrative actions or after resolving false positives.
        
        Args:
            user: User object to reset limits for
        """
        # Clear all cache keys for this user
        cache_keys = [
            f'session_creation_limit:{user.id}',
            # Note: Can't easily clear all ws_message_limit and join_attempt_limit keys
            # without knowing all session IDs, but they will expire naturally
        ]
        
        for key in cache_keys:
            cache.delete(key)
        
        logger.info(f"Rate limits reset for user {user.username}")
    
    @staticmethod
    def get_user_rate_limit_status(user):
        """
        Get current rate limit status for a user.
        
        Args:
            user: User object to check
            
        Returns:
            dict: Dictionary containing rate limit status for all limits
        """
        session_creation_key = f'session_creation_limit:{user.id}'
        session_creation_count = cache.get(session_creation_key, 0)
        session_creation_ttl = cache.ttl(session_creation_key)
        
        return {
            'session_creation': {
                'current': session_creation_count,
                'limit': VideoSessionRateLimiter.SESSION_CREATION_LIMIT,
                'remaining': max(0, VideoSessionRateLimiter.SESSION_CREATION_LIMIT - session_creation_count),
                'reset_in_seconds': session_creation_ttl if session_creation_ttl else 0,
                'is_limited': session_creation_count >= VideoSessionRateLimiter.SESSION_CREATION_LIMIT
            }
        }


class SessionAbuseDetector:
    """
    Detects and tracks potential abuse patterns in video sessions.
    """
    
    @staticmethod
    def track_rapid_session_creation(user):
        """
        Track rapid session creation patterns that might indicate abuse.
        
        Args:
            user: User object creating sessions
            
        Returns:
            bool: True if pattern is suspicious
        """
        from .models import VideoSession
        
        # Check how many sessions created in last 10 minutes
        recent_threshold = timezone.now() - timedelta(minutes=10)
        recent_sessions = VideoSession.objects.filter(
            host=user,
            created_at__gte=recent_threshold
        ).count()
        
        # Flag if more than 5 sessions in 10 minutes
        if recent_sessions > 5:
            logger.warning(
                f"Suspicious rapid session creation detected for user {user.username}: "
                f"{recent_sessions} sessions in 10 minutes"
            )
            return True
        
        return False
    
    @staticmethod
    def track_repeated_join_leave(user, session_id):
        """
        Track repeated join/leave patterns that might indicate disruption.
        
        Args:
            user: User object
            session_id: UUID of the session
            
        Returns:
            bool: True if pattern is suspicious
        """
        cache_key = f'join_leave_pattern:{user.id}:{session_id}'
        
        # Track join/leave events in a list
        events = cache.get(cache_key, [])
        events.append({
            'timestamp': timezone.now().isoformat(),
            'action': 'join_leave'
        })
        
        # Keep only last 10 events
        events = events[-10:]
        
        # Store back in cache with 5 minute expiry
        cache.set(cache_key, events, 300)
        
        # Flag if more than 5 join/leave cycles in 5 minutes
        if len(events) > 5:
            logger.warning(
                f"Suspicious join/leave pattern detected for user {user.username} in session {session_id}: "
                f"{len(events)} cycles"
            )
            return True
        
        return False
    
    @staticmethod
    def track_session_disruption(user, session_id, disruption_type):
        """
        Track disruptive behavior in sessions.
        
        Args:
            user: User object
            session_id: UUID of the session
            disruption_type: Type of disruption (e.g., 'spam', 'inappropriate')
            
        Returns:
            int: Total disruption count for this user
        """
        cache_key = f'session_disruption:{user.id}'
        
        # Get current disruption count
        disruptions = cache.get(cache_key, [])
        disruptions.append({
            'timestamp': timezone.now().isoformat(),
            'session_id': str(session_id),
            'type': disruption_type
        })
        
        # Keep only last 24 hours of disruptions
        cutoff_time = timezone.now() - timedelta(hours=24)
        disruptions = [
            d for d in disruptions
            if timezone.datetime.fromisoformat(d['timestamp']) > cutoff_time
        ]
        
        # Store back in cache with 24 hour expiry
        cache.set(cache_key, disruptions, 86400)
        
        # Log if significant disruption count
        if len(disruptions) >= 3:
            logger.warning(
                f"Multiple disruptions detected for user {user.username}: "
                f"{len(disruptions)} incidents in 24 hours"
            )
        
        return len(disruptions)
    
    @staticmethod
    def is_user_flagged(user):
        """
        Check if user has been flagged for abuse.
        
        Args:
            user: User object to check
            
        Returns:
            tuple: (is_flagged: bool, reason: str or None)
        """
        cache_key = f'user_flagged:{user.id}'
        flag_data = cache.get(cache_key)
        
        if flag_data:
            return True, flag_data.get('reason', 'Flagged for abuse')
        
        return False, None
    
    @staticmethod
    def flag_user(user, reason, duration_hours=24):
        """
        Flag a user for abusive behavior.
        
        Args:
            user: User object to flag
            reason: Reason for flagging
            duration_hours: How long to keep the flag (default 24 hours)
        """
        cache_key = f'user_flagged:{user.id}'
        flag_data = {
            'reason': reason,
            'flagged_at': timezone.now().isoformat(),
            'flagged_by': 'system'
        }
        
        cache.set(cache_key, flag_data, duration_hours * 3600)
        
        logger.warning(
            f"User {user.username} flagged for abuse: {reason}. "
            f"Flag duration: {duration_hours} hours"
        )
    
    @staticmethod
    def unflag_user(user):
        """
        Remove abuse flag from a user.
        
        Args:
            user: User object to unflag
        """
        cache_key = f'user_flagged:{user.id}'
        cache.delete(cache_key)
        
        logger.info(f"Abuse flag removed for user {user.username}")
