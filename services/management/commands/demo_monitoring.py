"""
Management command to generate sample monitoring data for demonstration.
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

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of sample records to generate (default: 10)'
        )

    def handle(self, *args, **options):
        count = options['count']
        self.stdout.write(f'Generating {count} sample monitoring records...')
        
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
        for i in range(count):
            with monitoring.correlation_context():
                duration = random.uniform(0.1, 3.0)
                monitoring.log_performance(
                    f'demo_operation_{i % 3}',
                    duration,
                    {'iteration': i, 'random_value': random.randint(1, 100)}
                )
        
        # Generate error logs
        self.stdout.write('Generating error logs...')
        for i in range(max(1, count // 3)):
            with monitoring.correlation_context():
                error = ValueError(f'Demo error {i}')
                monitoring.log_error(
                    error,
                    {'demo_context': f'context_{i}', 'user_id': user.id}
                )
        
        # Generate user activity logs
        self.stdout.write('Generating user activity logs...')
        activities = ['login', 'content_upload', 'quiz_attempt', 'lesson_complete', 'dashboard_view']
        for i in range(count * 2):
            activity = random.choice(activities)
            monitoring.log_user_activity(
                user.id,
                activity,
                {'page': f'page_{i}', 'session_id': f'session_{i % 3}'}
            )
        
        # Generate AI processing metrics
        self.stdout.write('Generating AI processing metrics...')
        operations = ['summary', 'quiz', 'flashcard']
        for i in range(count):
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
            self.style.SUCCESS(f'Generated {count} sample monitoring records successfully!')
        )
        self.stdout.write('You can now view the monitoring dashboard at /services/monitoring/')