"""
Views for monitoring and analytics dashboard.
"""

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.db.models import Count, Avg, Sum, Q
from django.db import models
from django.utils import timezone
from datetime import timedelta, datetime
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from .models import (
    PerformanceLog, ErrorLog, UserActivityLog, 
    SystemMetrics, AlertLog, AIProcessingMetrics
)
from .monitoring import PerformanceMetrics
import json

User = get_user_model()


@staff_member_required
def monitoring_dashboard(request):
    """Main monitoring dashboard view."""
    # Get time range from request
    hours = int(request.GET.get('hours', 24))
    end_time = timezone.now()
    start_time = end_time - timedelta(hours=hours)
    
    # Performance metrics
    performance_stats = PerformanceMetrics.get_ai_processing_stats(hours)
    
    # Error statistics
    error_stats = PerformanceMetrics.get_error_stats(hours)
    
    # User activity stats
    active_users = UserActivityLog.objects.filter(
        timestamp__gte=start_time
    ).values('user').distinct().count()
    
    total_activities = UserActivityLog.objects.filter(
        timestamp__gte=start_time
    ).count()
    
    # Recent alerts
    recent_alerts = AlertLog.objects.filter(
        status__in=['open', 'acknowledged']
    ).order_by('-timestamp')[:10]
    
    # System health indicators
    health_indicators = {
        'ai_processing_health': 'good' if performance_stats['success_rate'] > 95 else 'warning',
        'error_rate_health': 'good' if error_stats['total_errors'] < 50 else 'warning',
        'user_activity_health': 'good' if active_users > 0 else 'warning',
    }
    
    context = {
        'performance_stats': performance_stats,
        'error_stats': error_stats,
        'active_users': active_users,
        'total_activities': total_activities,
        'recent_alerts': recent_alerts,
        'health_indicators': health_indicators,
        'time_range': hours,
    }
    
    return render(request, 'services/monitoring_dashboard.html', context)


@staff_member_required
def performance_metrics_api(request):
    """API endpoint for performance metrics data."""
    hours = int(request.GET.get('hours', 24))
    end_time = timezone.now()
    start_time = end_time - timedelta(hours=hours)
    
    # Get performance data by hour
    performance_data = []
    for i in range(hours):
        hour_start = start_time + timedelta(hours=i)
        hour_end = hour_start + timedelta(hours=1)
        
        hour_metrics = PerformanceLog.objects.filter(
            timestamp__gte=hour_start,
            timestamp__lt=hour_end
        ).aggregate(
            avg_duration=Avg('duration'),
            count=Count('id')
        )
        
        performance_data.append({
            'hour': hour_start.strftime('%Y-%m-%d %H:00'),
            'avg_duration': hour_metrics['avg_duration'] or 0,
            'count': hour_metrics['count']
        })
    
    return JsonResponse({'performance_data': performance_data})


@staff_member_required
def error_metrics_api(request):
    """API endpoint for error metrics data."""
    hours = int(request.GET.get('hours', 24))
    end_time = timezone.now()
    start_time = end_time - timedelta(hours=hours)
    
    # Get error data by hour
    error_data = []
    for i in range(hours):
        hour_start = start_time + timedelta(hours=i)
        hour_end = hour_start + timedelta(hours=1)
        
        hour_errors = ErrorLog.objects.filter(
            timestamp__gte=hour_start,
            timestamp__lt=hour_end
        ).count()
        
        error_data.append({
            'hour': hour_start.strftime('%Y-%m-%d %H:00'),
            'count': hour_errors
        })
    
    # Get error types distribution
    error_types = ErrorLog.objects.filter(
        timestamp__gte=start_time
    ).values('error_type').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    return JsonResponse({
        'error_data': error_data,
        'error_types': list(error_types)
    })


@staff_member_required
def user_activity_api(request):
    """API endpoint for user activity data."""
    hours = int(request.GET.get('hours', 24))
    end_time = timezone.now()
    start_time = end_time - timedelta(hours=hours)
    
    # Get activity data by hour
    activity_data = []
    for i in range(hours):
        hour_start = start_time + timedelta(hours=i)
        hour_end = hour_start + timedelta(hours=1)
        
        hour_activities = UserActivityLog.objects.filter(
            timestamp__gte=hour_start,
            timestamp__lt=hour_end
        ).count()
        
        unique_users = UserActivityLog.objects.filter(
            timestamp__gte=hour_start,
            timestamp__lt=hour_end
        ).values('user').distinct().count()
        
        activity_data.append({
            'hour': hour_start.strftime('%Y-%m-%d %H:00'),
            'activities': hour_activities,
            'unique_users': unique_users
        })
    
    # Get activity types distribution
    activity_types = UserActivityLog.objects.filter(
        timestamp__gte=start_time
    ).values('activity_type').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    return JsonResponse({
        'activity_data': activity_data,
        'activity_types': list(activity_types)
    })


@staff_member_required
def ai_processing_metrics_api(request):
    """API endpoint for AI processing metrics."""
    hours = int(request.GET.get('hours', 24))
    end_time = timezone.now()
    start_time = end_time - timedelta(hours=hours)
    
    # Get AI processing metrics
    ai_metrics = AIProcessingMetrics.objects.filter(
        timestamp__gte=start_time
    ).aggregate(
        total_operations=Count('id'),
        avg_processing_time=Avg('processing_time'),
        success_rate=Avg('success') * 100,
        total_tokens=Sum('tokens_used'),
        total_cost=Sum('cost_estimate')
    )
    
    # Get metrics by operation type
    operation_metrics = AIProcessingMetrics.objects.filter(
        timestamp__gte=start_time
    ).values('operation_type').annotate(
        count=Count('id'),
        avg_time=Avg('processing_time'),
        success_rate=Avg('success') * 100
    ).order_by('-count')
    
    # Get processing time distribution over time
    processing_timeline = []
    for i in range(0, hours, max(1, hours // 24)):  # Max 24 data points
        hour_start = start_time + timedelta(hours=i)
        hour_end = hour_start + timedelta(hours=max(1, hours // 24))
        
        hour_metrics = AIProcessingMetrics.objects.filter(
            timestamp__gte=hour_start,
            timestamp__lt=hour_end
        ).aggregate(
            avg_time=Avg('processing_time'),
            count=Count('id')
        )
        
        processing_timeline.append({
            'time': hour_start.strftime('%Y-%m-%d %H:00'),
            'avg_time': hour_metrics['avg_time'] or 0,
            'count': hour_metrics['count']
        })
    
    return JsonResponse({
        'ai_metrics': ai_metrics,
        'operation_metrics': list(operation_metrics),
        'processing_timeline': processing_timeline
    })


@staff_member_required
def alerts_list(request):
    """View for alerts management."""
    status_filter = request.GET.get('status', 'open')
    severity_filter = request.GET.get('severity', '')
    
    alerts = AlertLog.objects.all()
    
    if status_filter:
        alerts = alerts.filter(status=status_filter)
    if severity_filter:
        alerts = alerts.filter(severity=severity_filter)
    
    alerts = alerts.order_by('-timestamp')
    
    paginator = Paginator(alerts, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'severity_filter': severity_filter,
        'status_choices': AlertLog.STATUS_CHOICES,
        'severity_choices': AlertLog.SEVERITY_CHOICES,
    }
    
    return render(request, 'services/alerts_list.html', context)


@staff_member_required
def system_health_api(request):
    """API endpoint for system health status."""
    # Calculate health indicators
    now = timezone.now()
    last_hour = now - timedelta(hours=1)
    
    # Error rate health
    recent_errors = ErrorLog.objects.filter(timestamp__gte=last_hour).count()
    error_health = 'good' if recent_errors < 10 else 'warning' if recent_errors < 50 else 'critical'
    
    # AI processing health
    ai_metrics = AIProcessingMetrics.objects.filter(
        timestamp__gte=last_hour
    ).aggregate(
        success_rate=Avg('success'),
        avg_time=Avg('processing_time')
    )
    
    ai_success_rate = (ai_metrics['success_rate'] or 1) * 100
    ai_avg_time = ai_metrics['avg_time'] or 0
    
    ai_health = 'good'
    if ai_success_rate < 95 or ai_avg_time > 30:
        ai_health = 'warning'
    if ai_success_rate < 90 or ai_avg_time > 60:
        ai_health = 'critical'
    
    # User activity health
    active_users = UserActivityLog.objects.filter(
        timestamp__gte=last_hour
    ).values('user').distinct().count()
    
    activity_health = 'good' if active_users > 0 else 'warning'
    
    # Open alerts
    open_alerts = AlertLog.objects.filter(status='open').count()
    critical_alerts = AlertLog.objects.filter(
        status='open', 
        severity='critical'
    ).count()
    
    alert_health = 'good'
    if open_alerts > 5 or critical_alerts > 0:
        alert_health = 'warning'
    if critical_alerts > 2:
        alert_health = 'critical'
    
    return JsonResponse({
        'overall_health': 'good',  # Would be calculated based on all indicators
        'indicators': {
            'errors': {
                'status': error_health,
                'value': recent_errors,
                'description': f'{recent_errors} errors in last hour'
            },
            'ai_processing': {
                'status': ai_health,
                'value': f'{ai_success_rate:.1f}%',
                'description': f'{ai_success_rate:.1f}% success rate, {ai_avg_time:.1f}s avg time'
            },
            'user_activity': {
                'status': activity_health,
                'value': active_users,
                'description': f'{active_users} active users in last hour'
            },
            'alerts': {
                'status': alert_health,
                'value': open_alerts,
                'description': f'{open_alerts} open alerts ({critical_alerts} critical)'
            }
        }
    })


@staff_member_required
def logs_viewer(request):
    """View for browsing logs."""
    log_type = request.GET.get('type', 'performance')
    page = int(request.GET.get('page', 1))
    
    if log_type == 'performance':
        logs = PerformanceLog.objects.all().order_by('-timestamp')
    elif log_type == 'errors':
        logs = ErrorLog.objects.all().order_by('-timestamp')
    elif log_type == 'activity':
        logs = UserActivityLog.objects.all().order_by('-timestamp')
    else:
        logs = PerformanceLog.objects.none()
    
    paginator = Paginator(logs, 50)
    page_obj = paginator.get_page(page)
    
    context = {
        'page_obj': page_obj,
        'log_type': log_type,
        'log_types': [
            ('performance', 'Performance'),
            ('errors', 'Errors'),
            ('activity', 'User Activity'),
        ]
    }
    
    return render(request, 'services/logs_viewer.html', context)