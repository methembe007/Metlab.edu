"""
Demonstration script for the monitoring and logging system.
Run this to generate sample monitoring data.
"""

import time
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from services.monitoring import monitoring, monitor_performance, monitor_ai_processing
from services.models import AIProcessingMetrics, AlertLog

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate sample monitoring data for demonstration'

    def handle(self, *args, **options):
        self.stdout.write('Generating sample monitoring data...')
        
        # Create a test user if needed
        user, created = User.objects.get_or_create(
            username='demo_user',
            defaults={
                'email': 'demo@example.com',
                'first_name': 'Demo',
                'last_name': 'User'
            }
        )
        
        if created:
            user.set_password('demo123')
            user.save()
            self.stdout.write(f'Created demo user: {user.username}')
        
        # Generate performance logs
        self.stdout.write('Generating performance logs...')
        for i in range(10):
            with monitoring.correlation_context():
                duration = random.uniform(0.1, 3.0)
                monitoring.log_performance(
                    f'demo_operation_{i % 3}',
                    duration,
                    {'iteration': i, 'random_value': random.randint(1, 100)}
                )
        
        # Generate error logs
        self.stdout.write('Generating error logs...')
        for i in range(3):
            with monitoring.correlation_context():
                error = ValueError(f'Demo error {i}')
                monitoring.log_error(
                    error,
                    {'demo_context': f'context_{i}', 'user_id': user.id}
                )
        
        # Generate user activity logs
        self.stdout.write('Generating user activity logs...')
        activities = ['login', 'content_upload', 'quiz_attempt', 'lesson_complete', 'dashboard_view']
        for i in range(15):
            activity = random.choice(activities)
            monitoring.log_user_activity(
                user.id,
                activity,
                {'page': f'page_{i}', 'session_id': f'session_{i % 3}'}
            )
        
        # Generate AI processing metrics
        self.stdout.write('Generating AI processing metrics...')
        operations = ['summary', 'quiz', 'flashcard']
        for i in range(8):
            operation = random.choice(operations)
            success = random.choice([True, True, True, False])  # 75% success rate
            
            AIProcessingMetrics.objects.create(
                operation_type=operation,
                content_type='pdf',
                processing_time=random.uniform(1.0, 10.0),
                input_size=random.randint(1000, 10000),
                output_size=random.randint(100, 2000),
                success=success,
                error_message='' if success else f'Demo AI error for {operation}',
                correlation_id=monitoring.generate_correlation_id(),
                user=user,
                api_calls_made=random.randint(1, 3),
                tokens_used=random.randint(100, 1000) if success else None,
                cost_estimate=random.uniform(0.01, 0.50) if success else None
            )
        
        # Generate some alerts
        self.stdout.write('Generating sample alerts...')
        alert_types = [
            ('high_error_rate', 'High Error Rate Detected', 'medium'),
            ('slow_ai_processing', 'Slow AI Processing', 'low'),
            ('system_overload', 'System Overload Warning', 'high')
        ]
        
        for alert_type, title, severity in alert_types:
            AlertLog.objects.create(
                alert_type=alert_type,
                title=title,
                description=f'Demo alert: {title} - This is a demonstration alert.',
                severity=severity,
                correlation_id=monitoring.generate_correlation_id(),
                metadata={'demo': True, 'generated_by': 'demo_script'}
            )
        
        self.stdout.write(
            self.style.SUCCESS('Sample monitoring data generated successfully!')
        )
        self.stdout.write('You can now view the monitoring dashboard at /services/monitoring/')


# Demonstration functions with monitoring decorators
@monitor_performance('demo_slow_operation')
def demo_slow_operation():
    """Simulate a slow operation."""
    time.sleep(random.uniform(1.0, 3.0))
    return "slow_operation_complete"


@monitor_ai_processing
def demo_ai_processing():
    """Simulate AI processing."""
    time.sleep(random.uniform(0.5, 2.0))
    if random.random() < 0.8:  # 80% success rate
        return {"summary": "This is a demo AI-generated summary"}
    else:
        raise Exception("Demo AI processing error")


def run_demo_operations():
    """Run demonstration operations with monitoring."""
    print("Running demo operations with monitoring...")
    
    # Run some monitored operations
    for i in range(5):
        try:
            with monitoring.correlation_context():
                result = demo_slow_operation()
                print(f"Operation {i}: {result}")
        except Exception as e:
            monitoring.log_error(e, {'operation_index': i})
    
    # Run some AI operations
    for i in range(3):
        try:
            with monitoring.correlation_context():
                result = demo_ai_processing()
                print(f"AI Operation {i}: Success")
        except Exception as e:
            monitoring.log_error(e, {'ai_operation_index': i})
            print(f"AI Operation {i}: Failed - {e}")


if __name__ == '__main__':
    # This allows running the script directly for testing
    import django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'metlab_edu.settings')
    django.setup()
    
    run_demo_operations()