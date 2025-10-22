"""
Health check views for production monitoring.
"""

import json
import time
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import redis


@never_cache
@require_http_methods(["GET"])
def health_check(request):
    """
    Comprehensive health check endpoint for monitoring.
    Returns JSON with status of all critical services.
    """
    start_time = time.time()
    health_status = {
        'status': 'healthy',
        'timestamp': time.time(),
        'services': {},
        'response_time_ms': 0
    }
    
    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status['services']['database'] = {
            'status': 'healthy',
            'message': 'Database connection successful'
        }
    except Exception as e:
        health_status['services']['database'] = {
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)}'
        }
        health_status['status'] = 'unhealthy'
    
    # Check Redis cache connectivity
    try:
        cache.set('health_check', 'test', 10)
        test_value = cache.get('health_check')
        if test_value == 'test':
            health_status['services']['cache'] = {
                'status': 'healthy',
                'message': 'Cache connection successful'
            }
        else:
            raise Exception('Cache test failed')
    except Exception as e:
        health_status['services']['cache'] = {
            'status': 'unhealthy',
            'message': f'Cache connection failed: {str(e)}'
        }
        health_status['status'] = 'unhealthy'
    
    # Check Redis broker (for Celery) - only if Redis is available
    try:
        if hasattr(settings, 'CELERY_BROKER_URL') and getattr(settings, 'REDIS_AVAILABLE', False):
            if settings.CELERY_BROKER_URL.startswith('redis://'):
                redis_client = redis.from_url(settings.CELERY_BROKER_URL)
                redis_client.ping()
                health_status['services']['message_broker'] = {
                    'status': 'healthy',
                    'message': 'Message broker connection successful'
                }
            else:
                health_status['services']['message_broker'] = {
                    'status': 'healthy',
                    'message': 'Using database broker (Redis not available)'
                }
        else:
            health_status['services']['message_broker'] = {
                'status': 'skipped',
                'message': 'Message broker not configured or Redis not available'
            }
    except Exception as e:
        health_status['services']['message_broker'] = {
            'status': 'degraded',
            'message': f'Message broker connection failed, using fallback: {str(e)}'
        }
        # Don't mark as unhealthy if we have fallback
    
    # Calculate response time
    end_time = time.time()
    health_status['response_time_ms'] = round((end_time - start_time) * 1000, 2)
    
    # Return appropriate HTTP status code
    status_code = 200 if health_status['status'] == 'healthy' else 503
    
    return JsonResponse(health_status, status=status_code)


@never_cache
@require_http_methods(["GET"])
def readiness_check(request):
    """
    Readiness check for Kubernetes/container orchestration.
    Returns 200 if the application is ready to serve traffic.
    """
    try:
        # Quick database check
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        # Quick cache check
        cache.set('readiness_check', 'ready', 5)
        
        return JsonResponse({
            'status': 'ready',
            'timestamp': time.time()
        })
    except Exception as e:
        return JsonResponse({
            'status': 'not_ready',
            'error': str(e),
            'timestamp': time.time()
        }, status=503)


@never_cache
@require_http_methods(["GET"])
def liveness_check(request):
    """
    Liveness check for Kubernetes/container orchestration.
    Returns 200 if the application is alive (basic functionality).
    """
    return JsonResponse({
        'status': 'alive',
        'timestamp': time.time()
    })


@never_cache
@require_http_methods(["GET"])
def metrics(request):
    """
    Basic metrics endpoint for monitoring.
    """
    try:
        # Database metrics
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM django_session")
            active_sessions = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM accounts_user")
            total_users = cursor.fetchone()[0]
        
        # Cache metrics
        cache_info = {}
        try:
            if getattr(settings, 'REDIS_AVAILABLE', False) and hasattr(cache, '_cache') and hasattr(cache._cache, 'get_client'):
                redis_client = cache._cache.get_client()
                redis_info = redis_client.info()
                cache_info = {
                    'used_memory': redis_info.get('used_memory', 0),
                    'connected_clients': redis_info.get('connected_clients', 0),
                    'keyspace_hits': redis_info.get('keyspace_hits', 0),
                    'keyspace_misses': redis_info.get('keyspace_misses', 0)
                }
            else:
                cache_info = {'backend': 'local_memory', 'redis_available': False}
        except:
            cache_info = {'error': 'Unable to retrieve cache metrics', 'backend': 'fallback'}
        
        metrics_data = {
            'timestamp': time.time(),
            'database': {
                'active_sessions': active_sessions,
                'total_users': total_users
            },
            'cache': cache_info,
            'application': {
                'debug_mode': settings.DEBUG,
                'django_version': getattr(settings, 'DJANGO_VERSION', 'unknown')
            }
        }
        
        return JsonResponse(metrics_data)
    except Exception as e:
        return JsonResponse({
            'error': f'Unable to retrieve metrics: {str(e)}',
            'timestamp': time.time()
        }, status=500)