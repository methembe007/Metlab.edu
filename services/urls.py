"""
URL configuration for monitoring and analytics services.
"""

from django.urls import path
from . import analytics_views

app_name = 'services'

urlpatterns = [
    # Dashboard views
    path('monitoring/', analytics_views.monitoring_dashboard, name='monitoring_dashboard'),
    path('alerts/', analytics_views.alerts_list, name='alerts_list'),
    path('logs/', analytics_views.logs_viewer, name='logs_viewer'),
    
    # API endpoints for dashboard data
    path('api/performance-metrics/', analytics_views.performance_metrics_api, name='performance_metrics_api'),
    path('api/error-metrics/', analytics_views.error_metrics_api, name='error_metrics_api'),
    path('api/user-activity/', analytics_views.user_activity_api, name='user_activity_api'),
    path('api/ai-processing-metrics/', analytics_views.ai_processing_metrics_api, name='ai_processing_metrics_api'),
    path('api/system-health/', analytics_views.system_health_api, name='system_health_api'),
]