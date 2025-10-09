"""
Tests for monitoring and logging system.
"""

import time
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import patch, MagicMock

from .monitoring import (
    monitoring, monitor_performance, monitor_ai_processing, 
    log_user_activity, PerformanceMetrics
)
from .models import PerformanceLog, ErrorLog, UserActivityLog, AIProcessingMetrics
from .analytics_views import monitoring_dashboard

User = get_user_model()


class MonitoringServiceTest(TestCase):
    """Test monitoring service functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_correlation_id_generation(self):
        """Test correlation ID generation and context management."""
        correlation_id = monitoring.generate_correlation_id()
        self.assertIsInstance(correlation_id, str)
        self.assertEqual(len(correlation_id), 36)  # UUID4 length
        
        # Test context manager
        with monitoring.correlation_context() as ctx_id:
            self.assertEqual(monitoring.get_correlation_id(), ctx_id)
    
    def test_performance_monitoring_decorator(self):
        """Test performance monitoring decorator."""
        @monitor_performance('test_operation')
        def test_function():
            time.sleep(0.1)
            return "test_result"
        
        result = test_function()
        self.assertEqual(result, "test_result")
        
        # Check if performance was logged
        self.assertTrue(PerformanceLog.objects.filter(
            operation='test_operation'
        ).exists())
    
    def test_ai_processing_monitoring(self):
        """Test AI processing monitoring decorator."""
        @monitor_ai_processing
        def test_ai_function():
            time.sleep(0.05)
            return {"result": "ai_output"}
        
        result = test_ai_function()
        self.assertEqual(result, {"result": "ai_output"})
        
        # Check if AI processing was logged
        self.assertTrue(PerformanceLog.objects.filter(
            operation='ai_processing.test_ai_function'
        ).exists())
    
    def test_error_logging(self):
        """Test error logging functionality."""
        test_error = ValueError("Test error")
        context = {"test_key": "test_value"}
        
        monitoring.log_error(test_error, context)
        
        # Check if error was logged
        error_log = ErrorLog.objects.filter(
            error_type='ValueError',
            error_message='Test error'
        ).first()
        
        self.assertIsNotNone(error_log)
        self.assertEqual(error_log.context, context)
    
    def test_user_activity_logging(self):
        """Test user activity logging."""
        activity = "test_activity"
        metadata = {"page": "test_page"}
        
        monitoring.log_user_activity(self.user.id, activity, metadata)
        
        # Check if activity was logged
        activity_log = UserActivityLog.objects.filter(
            user=self.user,
            activity_type=activity
        ).first()
        
        self.assertIsNotNone(activity_log)
        self.assertEqual(activity_log.metadata, metadata)
    
    def test_user_activity_decorator(self):
        """Test user activity logging decorator."""
        factory = RequestFactory()
        request = factory.get('/test/')
        request.user = self.user
        
        @log_user_activity('page_view', {'page': 'test'})
        def test_view(request):
            return "view_result"
        
        result = test_view(request)
        self.assertEqual(result, "view_result")
        
        # Check if activity was logged
        self.assertTrue(UserActivityLog.objects.filter(
            user=self.user,
            activity_type='page_view'
        ).exists())


class AnalyticsViewsTest(TestCase):
    """Test analytics dashboard views."""
    
    def setUp(self):
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        # Create some test data
        PerformanceLog.objects.create(
            operation='test_operation',
            duration=1.5,
            correlation_id='test-correlation-id',
            user=self.user
        )
        
        ErrorLog.objects.create(
            error_type='TestError',
            error_message='Test error message',
            correlation_id='test-correlation-id',
            user=self.user
        )
        
        UserActivityLog.objects.create(
            user=self.user,
            activity_type='test_activity',
            correlation_id='test-correlation-id'
        )
    
    def test_monitoring_dashboard_access(self):
        """Test monitoring dashboard access."""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get('/services/monitoring/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'System Monitoring Dashboard')
    
    def test_performance_metrics_api(self):
        """Test performance metrics API endpoint."""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get('/services/api/performance-metrics/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('performance_data', data)
        self.assertIsInstance(data['performance_data'], list)
    
    def test_error_metrics_api(self):
        """Test error metrics API endpoint."""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get('/services/api/error-metrics/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('error_data', data)
        self.assertIn('error_types', data)
    
    def test_user_activity_api(self):
        """Test user activity API endpoint."""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get('/services/api/user-activity/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('activity_data', data)
        self.assertIn('activity_types', data)
    
    def test_system_health_api(self):
        """Test system health API endpoint."""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get('/services/api/system-health/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('overall_health', data)
        self.assertIn('indicators', data)


class PerformanceMetricsTest(TestCase):
    """Test performance metrics calculations."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test AI processing metrics
        AIProcessingMetrics.objects.create(
            operation_type='summary',
            content_type='pdf',
            processing_time=2.5,
            input_size=1000,
            output_size=200,
            success=True,
            user=self.user,
            correlation_id='test-id-1'
        )
        
        AIProcessingMetrics.objects.create(
            operation_type='quiz',
            content_type='text',
            processing_time=3.0,
            input_size=1500,
            output_size=300,
            success=False,
            error_message='Test error',
            user=self.user,
            correlation_id='test-id-2'
        )
    
    def test_ai_processing_stats(self):
        """Test AI processing statistics calculation."""
        stats = PerformanceMetrics.get_ai_processing_stats(24)
        
        self.assertIn('total_operations', stats)
        self.assertIn('average_duration', stats)
        self.assertIn('success_rate', stats)
        self.assertIn('error_count', stats)
        
        # Should have 2 operations, 1 success, 1 error
        self.assertEqual(stats['total_operations'], 2)
        self.assertEqual(stats['error_count'], 1)
        self.assertEqual(stats['success_rate'], 50.0)  # 1 out of 2 successful
    
    def test_error_stats(self):
        """Test error statistics calculation."""
        # Create an error log
        ErrorLog.objects.create(
            error_type='TestError',
            error_message='Test error',
            correlation_id='test-correlation-id'
        )
        
        stats = PerformanceMetrics.get_error_stats(24)
        
        self.assertIn('total_errors', stats)
        self.assertIn('error_rate', stats)
        self.assertIn('errors_by_hour', stats)
        
        self.assertGreaterEqual(stats['total_errors'], 1)