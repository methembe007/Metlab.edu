"""
Monitoring and logging service for Metlab.edu platform.
Provides structured logging, performance monitoring, and error tracking.
"""

import logging
import time
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from functools import wraps
from contextlib import contextmanager
from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.utils import timezone
import threading

# Thread-local storage for correlation IDs
_local = threading.local()


class CorrelationIDFilter(logging.Filter):
    """Add correlation ID to log records."""
    
    def filter(self, record):
        record.correlation_id = getattr(_local, 'correlation_id', 'no-correlation-id')
        return True


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'correlation_id': getattr(record, 'correlation_id', 'no-correlation-id'),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_path'):
            log_entry['request_path'] = record.request_path
        if hasattr(record, 'duration'):
            log_entry['duration'] = record.duration
        if hasattr(record, 'error_type'):
            log_entry['error_type'] = record.error_type
        if hasattr(record, 'performance_data'):
            log_entry['performance_data'] = record.performance_data
            
        return json.dumps(log_entry)


class MonitoringService:
    """Central monitoring service for the platform."""
    
    def __init__(self):
        self.logger = logging.getLogger('monitoring')
        self.performance_logger = logging.getLogger('performance')
        self.error_logger = logging.getLogger('errors')
        self.activity_logger = logging.getLogger('activity')
    
    @staticmethod
    def generate_correlation_id() -> str:
        """Generate a unique correlation ID."""
        return str(uuid.uuid4())
    
    @staticmethod
    def set_correlation_id(correlation_id: str):
        """Set correlation ID for current thread."""
        _local.correlation_id = correlation_id
    
    @staticmethod
    def get_correlation_id() -> str:
        """Get correlation ID for current thread."""
        return getattr(_local, 'correlation_id', 'no-correlation-id')
    
    @contextmanager
    def correlation_context(self, correlation_id: str = None):
        """Context manager for correlation ID."""
        if correlation_id is None:
            correlation_id = self.generate_correlation_id()
        
        old_id = getattr(_local, 'correlation_id', None)
        self.set_correlation_id(correlation_id)
        try:
            yield correlation_id
        finally:
            if old_id:
                _local.correlation_id = old_id
            else:
                if hasattr(_local, 'correlation_id'):
                    delattr(_local, 'correlation_id')
    
    def log_performance(self, operation: str, duration: float, 
                       metadata: Dict[str, Any] = None):
        """Log performance metrics."""
        extra = {
            'operation': operation,
            'duration': duration,
            'performance_data': metadata or {}
        }
        self.performance_logger.info(f"Performance: {operation}", extra=extra)
        
        # Store in database
        from .models import PerformanceLog
        PerformanceLog.objects.create(
            operation=operation,
            duration=duration,
            correlation_id=self.get_correlation_id(),
            metadata=metadata or {}
        )
        
        # Store in cache for dashboard
        cache_key = f"performance:{operation}:{timezone.now().strftime('%Y%m%d%H')}"
        performance_data = cache.get(cache_key, [])
        performance_data.append({
            'timestamp': timezone.now().isoformat(),
            'duration': duration,
            'metadata': metadata or {}
        })
        cache.set(cache_key, performance_data, 3600)  # 1 hour
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log error with context."""
        extra = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {}
        }
        self.error_logger.error(f"Error: {type(error).__name__}", extra=extra)
        
        # Store in database
        from .models import ErrorLog
        ErrorLog.objects.create(
            error_type=type(error).__name__,
            error_message=str(error),
            correlation_id=self.get_correlation_id(),
            context=context or {}
        )
        
        # Store error count in cache
        cache_key = f"errors:{timezone.now().strftime('%Y%m%d%H')}"
        error_count = cache.get(cache_key, 0)
        cache.set(cache_key, error_count + 1, 3600)
    
    def log_user_activity(self, user_id: int, activity: str, 
                         metadata: Dict[str, Any] = None):
        """Log user activity."""
        extra = {
            'user_id': user_id,
            'activity': activity,
            'metadata': metadata or {}
        }
        self.activity_logger.info(f"Activity: {activity}", extra=extra)
        
        # Store in database
        from .models import UserActivityLog
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(id=user_id)
            UserActivityLog.objects.create(
                user=user,
                activity_type=activity,
                correlation_id=self.get_correlation_id(),
                metadata=metadata or {}
            )
        except User.DoesNotExist:
            pass  # Skip if user doesn't exist
        
        # Store in cache for analytics
        cache_key = f"activity:{user_id}:{timezone.now().strftime('%Y%m%d')}"
        activities = cache.get(cache_key, [])
        activities.append({
            'timestamp': timezone.now().isoformat(),
            'activity': activity,
            'metadata': metadata or {}
        })
        cache.set(cache_key, activities, 86400)  # 24 hours


# Global monitoring service instance
monitoring = MonitoringService()


def monitor_performance(operation_name: str = None):
    """Decorator to monitor function performance."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                monitoring.log_performance(op_name, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                monitoring.log_performance(op_name, duration, {'error': str(e)})
                monitoring.log_error(e, {'function': op_name})
                raise
        return wrapper
    return decorator


def monitor_ai_processing(func):
    """Decorator specifically for AI processing functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        operation = f"ai_processing.{func.__name__}"
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Log AI processing metrics
            metadata = {
                'success': True,
                'result_size': len(str(result)) if result else 0
            }
            monitoring.log_performance(operation, duration, metadata)
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            metadata = {
                'success': False,
                'error': str(e)
            }
            monitoring.log_performance(operation, duration, metadata)
            monitoring.log_error(e, {'ai_operation': operation})
            raise
    return wrapper


def log_user_activity(activity: str, metadata: Dict[str, Any] = None):
    """Decorator to log user activity."""
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if hasattr(request, 'user') and request.user.is_authenticated:
                monitoring.log_user_activity(
                    request.user.id, 
                    activity, 
                    metadata
                )
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


class PerformanceMetrics:
    """Class to collect and analyze performance metrics."""
    
    @staticmethod
    def get_ai_processing_stats(hours: int = 24) -> Dict[str, Any]:
        """Get AI processing performance statistics."""
        stats = {
            'total_operations': 0,
            'average_duration': 0,
            'success_rate': 0,
            'error_count': 0,
            'operations_by_type': {}
        }
        
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Collect data from cache
        for hour in range(hours):
            hour_time = start_time + timedelta(hours=hour)
            cache_key = f"performance:ai_processing:{hour_time.strftime('%Y%m%d%H')}"
            hour_data = cache.get(cache_key, [])
            
            for entry in hour_data:
                stats['total_operations'] += 1
                if entry.get('metadata', {}).get('success', True):
                    stats['average_duration'] += entry['duration']
                else:
                    stats['error_count'] += 1
        
        if stats['total_operations'] > 0:
            stats['average_duration'] /= stats['total_operations']
            stats['success_rate'] = (
                (stats['total_operations'] - stats['error_count']) / 
                stats['total_operations'] * 100
            )
        
        return stats
    
    @staticmethod
    def get_error_stats(hours: int = 24) -> Dict[str, Any]:
        """Get error statistics."""
        stats = {
            'total_errors': 0,
            'error_rate': 0,
            'errors_by_hour': []
        }
        
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=hours)
        
        for hour in range(hours):
            hour_time = start_time + timedelta(hours=hour)
            cache_key = f"errors:{hour_time.strftime('%Y%m%d%H')}"
            error_count = cache.get(cache_key, 0)
            stats['total_errors'] += error_count
            stats['errors_by_hour'].append({
                'hour': hour_time.strftime('%Y-%m-%d %H:00'),
                'count': error_count
            })
        
        return stats
    
    @staticmethod
    def get_user_activity_stats(hours: int = 24) -> Dict[str, Any]:
        """Get user activity statistics."""
        stats = {
            'active_users': 0,
            'total_activities': 0,
            'activities_by_type': {},
            'activity_timeline': []
        }
        
        # This would typically query the database or cache
        # For now, return basic structure
        return stats


class AlertingService:
    """Service for handling alerts and notifications."""
    
    def __init__(self):
        self.logger = logging.getLogger('alerts')
        self.alert_thresholds = {
            'error_rate': 5,  # errors per hour
            'ai_processing_time': 30,  # seconds
            'response_time': 5,  # seconds
        }
    
    def check_error_rate(self):
        """Check if error rate exceeds threshold."""
        current_hour = timezone.now().strftime('%Y%m%d%H')
        cache_key = f"errors:{current_hour}"
        error_count = cache.get(cache_key, 0)
        
        if error_count > self.alert_thresholds['error_rate']:
            self.send_alert(
                'high_error_rate',
                f"Error rate exceeded threshold: {error_count} errors in current hour"
            )
    
    def check_ai_processing_performance(self):
        """Check AI processing performance."""
        stats = PerformanceMetrics.get_ai_processing_stats(1)  # Last hour
        
        if stats['average_duration'] > self.alert_thresholds['ai_processing_time']:
            self.send_alert(
                'slow_ai_processing',
                f"AI processing time exceeded threshold: {stats['average_duration']:.2f}s"
            )
    
    def send_alert(self, alert_type: str, message: str):
        """Send alert notification."""
        alert_data = {
            'type': alert_type,
            'message': message,
            'timestamp': timezone.now().isoformat(),
            'correlation_id': monitoring.get_correlation_id()
        }
        
        self.logger.critical(f"ALERT: {alert_type}", extra=alert_data)
        
        # In production, this would send emails, Slack notifications, etc.
        # For now, just log the alert


# Global alerting service instance
alerting = AlertingService()