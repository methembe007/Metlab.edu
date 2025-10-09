"""
Rate limiting utilities and decorators for API endpoints
"""

from functools import wraps
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings
import time
import logging

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def rate_limit(key_func=None, rate='60/m', methods=['POST'], skip_if=None):
    """
    Rate limiting decorator
    
    Args:
        key_func: Function to generate cache key (default: uses IP)
        rate: Rate limit in format 'count/period' (e.g., '60/m', '1000/h', '10000/d')
        methods: HTTP methods to apply rate limiting to
        skip_if: Function that returns True to skip rate limiting
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Skip rate limiting if disabled in settings
            if not getattr(settings, 'RATE_LIMIT_ENABLE', True):
                return view_func(request, *args, **kwargs)
            
            # Skip if method not in rate limited methods
            if request.method not in methods:
                return view_func(request, *args, **kwargs)
            
            # Skip if skip_if function returns True
            if skip_if and skip_if(request):
                return view_func(request, *args, **kwargs)
            
            # Parse rate limit
            try:
                count, period = rate.split('/')
                count = int(count)
                
                if period == 'm':
                    window_seconds = 60
                elif period == 'h':
                    window_seconds = 3600
                elif period == 'd':
                    window_seconds = 86400
                else:
                    window_seconds = 60  # Default to minute
                    
            except ValueError:
                logger.error(f"Invalid rate format: {rate}")
                return view_func(request, *args, **kwargs)
            
            # Generate cache key
            if key_func:
                cache_key = key_func(request)
            else:
                client_ip = get_client_ip(request)
                cache_key = f"rate_limit_{client_ip}_{view_func.__name__}"
            
            # Get current window
            current_time = int(time.time())
            window_start = current_time - (current_time % window_seconds)
            window_key = f"{cache_key}_{window_start}"
            
            # Get current count
            current_count = cache.get(window_key, 0)
            
            # Check if rate limit exceeded
            if current_count >= count:
                logger.warning(f"Rate limit exceeded for key: {cache_key}")
                return JsonResponse({
                    'error': 'Rate limit exceeded. Please try again later.',
                    'code': 'RATE_LIMIT_EXCEEDED',
                    'retry_after': window_seconds - (current_time % window_seconds)
                }, status=429)
            
            # Increment counter
            cache.set(window_key, current_count + 1, window_seconds)
            
            # Call the original view
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def api_rate_limit(rate='30/m'):
    """Rate limiting specifically for API endpoints"""
    def key_func(request):
        client_ip = get_client_ip(request)
        return f"api_rate_limit_{client_ip}"
    
    return rate_limit(key_func=key_func, rate=rate, methods=['GET', 'POST', 'PUT', 'DELETE'])


def upload_rate_limit(rate='50/h'):
    """Rate limiting specifically for file uploads"""
    def key_func(request):
        client_ip = get_client_ip(request)
        return f"upload_rate_limit_{client_ip}"
    
    return rate_limit(key_func=key_func, rate=rate, methods=['POST'])


def login_rate_limit(rate='10/m'):
    """Rate limiting specifically for login attempts"""
    def key_func(request):
        client_ip = get_client_ip(request)
        return f"login_rate_limit_{client_ip}"
    
    return rate_limit(key_func=key_func, rate=rate, methods=['POST'])


def user_rate_limit(rate='100/h'):
    """Rate limiting per authenticated user"""
    def key_func(request):
        if request.user.is_authenticated:
            return f"user_rate_limit_{request.user.id}"
        else:
            client_ip = get_client_ip(request)
            return f"anon_rate_limit_{client_ip}"
    
    def skip_if(request):
        # Skip for superusers
        return request.user.is_authenticated and request.user.is_superuser
    
    return rate_limit(key_func=key_func, rate=rate, skip_if=skip_if)


class RateLimitMixin:
    """Mixin for class-based views to add rate limiting"""
    
    rate_limit_key = None
    rate_limit_rate = '60/m'
    rate_limit_methods = ['POST']
    
    def dispatch(self, request, *args, **kwargs):
        # Apply rate limiting
        if not getattr(settings, 'RATE_LIMIT_ENABLE', True):
            return super().dispatch(request, *args, **kwargs)
        
        if request.method in self.rate_limit_methods:
            # Generate cache key
            if self.rate_limit_key:
                cache_key = self.rate_limit_key
            else:
                client_ip = get_client_ip(request)
                cache_key = f"rate_limit_{client_ip}_{self.__class__.__name__}"
            
            # Parse rate limit
            try:
                count, period = self.rate_limit_rate.split('/')
                count = int(count)
                
                if period == 'm':
                    window_seconds = 60
                elif period == 'h':
                    window_seconds = 3600
                elif period == 'd':
                    window_seconds = 86400
                else:
                    window_seconds = 60
                    
            except ValueError:
                logger.error(f"Invalid rate format: {self.rate_limit_rate}")
                return super().dispatch(request, *args, **kwargs)
            
            # Check rate limit
            current_time = int(time.time())
            window_start = current_time - (current_time % window_seconds)
            window_key = f"{cache_key}_{window_start}"
            
            current_count = cache.get(window_key, 0)
            
            if current_count >= count:
                logger.warning(f"Rate limit exceeded for key: {cache_key}")
                return JsonResponse({
                    'error': 'Rate limit exceeded. Please try again later.',
                    'code': 'RATE_LIMIT_EXCEEDED',
                    'retry_after': window_seconds - (current_time % window_seconds)
                }, status=429)
            
            # Increment counter
            cache.set(window_key, current_count + 1, window_seconds)
        
        return super().dispatch(request, *args, **kwargs)