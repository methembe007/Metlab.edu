"""
Middleware for monitoring and logging correlation IDs.
"""

import time
from django.utils.deprecation import MiddlewareMixin
from services.monitoring import monitoring


class CorrelationIDMiddleware(MiddlewareMixin):
    """Middleware to add correlation IDs to requests."""
    
    def process_request(self, request):
        """Add correlation ID to request."""
        correlation_id = monitoring.generate_correlation_id()
        monitoring.set_correlation_id(correlation_id)
        request.correlation_id = correlation_id
        return None
    
    def process_response(self, request, response):
        """Add correlation ID to response headers."""
        if hasattr(request, 'correlation_id'):
            response['X-Correlation-ID'] = request.correlation_id
        return response


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """Middleware to monitor request performance."""
    
    def process_request(self, request):
        """Start timing the request."""
        request._monitoring_start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Log request performance."""
        if hasattr(request, '_monitoring_start_time'):
            duration = time.time() - request._monitoring_start_time
            
            # Log performance data
            metadata = {
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'user_id': request.user.id if request.user.is_authenticated else None,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'ip_address': self._get_client_ip(request)
            }
            
            monitoring.log_performance(
                f"request.{request.method}.{response.status_code}",
                duration,
                metadata
            )
            
            # Log slow requests
            if duration > 5.0:  # 5 seconds threshold
                monitoring.logger.warning(
                    f"Slow request: {request.method} {request.path}",
                    extra={
                        'duration': duration,
                        'request_path': request.path,
                        'user_id': request.user.id if request.user.is_authenticated else None
                    }
                )
        
        return response
    
    def process_exception(self, request, exception):
        """Log request exceptions."""
        if hasattr(request, '_monitoring_start_time'):
            duration = time.time() - request._monitoring_start_time
            
            context = {
                'method': request.method,
                'path': request.path,
                'duration': duration,
                'user_id': request.user.id if request.user.is_authenticated else None,
                'ip_address': self._get_client_ip(request)
            }
            
            monitoring.log_error(exception, context)
        
        return None
    
    def _get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserActivityMiddleware(MiddlewareMixin):
    """Middleware to track user activity."""
    
    def process_response(self, request, response):
        """Log user activity."""
        if request.user.is_authenticated and response.status_code < 400:
            activity_type = self._determine_activity_type(request)
            if activity_type:
                metadata = {
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code
                }
                monitoring.log_user_activity(
                    request.user.id,
                    activity_type,
                    metadata
                )
        
        return response
    
    def _determine_activity_type(self, request):
        """Determine activity type based on request."""
        path = request.path.lower()
        method = request.method.upper()
        
        # Map paths to activity types
        activity_mapping = {
            '/content/upload': 'content_upload',
            '/learning/lesson': 'lesson_access',
            '/learning/quiz': 'quiz_attempt',
            '/gamification/achievements': 'achievements_view',
            '/community/study-room': 'study_room_join',
            '/accounts/dashboard': 'dashboard_access',
        }
        
        for path_pattern, activity in activity_mapping.items():
            if path_pattern in path:
                return activity
        
        # Generic activities
        if method == 'POST':
            return 'form_submission'
        elif method == 'GET' and 'dashboard' in path:
            return 'dashboard_access'
        
        return None