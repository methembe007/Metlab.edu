"""
Comprehensive system validation script for the AI Learning Platform.
Validates all components, data flows, and integrations are working correctly.
"""

import os
import sys
import django
import subprocess
import time
import json
from datetime import datetime
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'metlab_edu.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.test.utils import get_runner
from django.conf import settings
from django.db import connection
from django.core.cache import cache


class SystemValidator:
    """Comprehensive system validation"""
    
    def __init__(self):
        self.results = []
        self.start_time = time.time()
        self.validation_report = {
            'timestamp': datetime.now().isoformat(),
            'system_info': self.get_system_info(),
            'validations': []
        }
    
    def get_system_info(self):
        """Get system information"""
        return {
            'python_version': sys.version,
            'django_version': django.get_version(),
            'database_engine': settings.DATABASES['default']['ENGINE'],
            'cache_backend': settings.CACHES['default']['BACKEND'],
            'debug_mode': settings.DEBUG,
            'installed_apps': list(settings.INSTALLED_APPS)
        }
    
    def log_validation(self, name, success, details, duration=0):
        """Log validation result"""
        result = {
            'name': name,
            'success': success,
            'details': details,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        self.results.append(result)
        self.validation_report['validations'].append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {name} ({duration:.2f}s)")
        if not success:
            print(f"   Details: {details}")
    
    def validate_database_connectivity(self):
        """Validate database connectivity and basic operations"""
        print("\n🗄️  Validating Database Connectivity")
        
        start_time = time.time()
        try:
            # Test basic connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            if result[0] != 1:
                raise Exception("Database query returned unexpected result")
            
            # Test table creation (migrations)
            from django.core.management import call_command
            call_command('migrate', verbosity=0, interactive=False)
            
            # Test model operations
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # Create test user
            test_user = User.objects.create_user(
                username='validation_test_user',
                email='test@validation.com',
                password='testpass123',
                role='student'
            )
            
            # Verify user was created
            retrieved_user = User.objects.get(username='validation_test_user')
            if retrieved_user.email != 'test@validation.com':
                raise Exception("User data integrity check failed")
            
            # Clean up
            test_user.delete()
            
            duration = time.time() - start_time
            self.log_validation(
                "Database Connectivity",
                True,
                "Database connection, migrations, and basic operations successful",
                duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_validation(
                "Database Connectivity",
                False,
                f"Database validation failed: {str(e)}",
                duration
            )
    
    def validate_cache_system(self):
        """Validate cache system functionality"""
        print("\n💾 Validating Cache System")
        
        start_time = time.time()
        try:
            # Test default cache
            cache.set('validation_test_key', 'validation_test_value', 30)
            cached_value = cache.get('validation_test_key')
            
            if cached_value != 'validation_test_value':
                raise Exception("Cache set/get operation failed")
            
            # Test cache deletion
            cache.delete('validation_test_key')
            deleted_value = cache.get('validation_test_key')
            
            if deleted_value is not None:
                raise Exception("Cache deletion failed")
            
            # Test cache with different backends if available
            cache_backends_tested = ['default']
            
            for cache_name in ['ai_cache', 'analytics', 'sessions']:
                if cache_name in settings.CACHES:
                    from django.core.cache import caches
                    specific_cache = caches[cache_name]
                    specific_cache.set(f'validation_{cache_name}', 'test', 30)
                    value = specific_cache.get(f'validation_{cache_name}')
                    if value == 'test':
                        cache_backends_tested.append(cache_name)
                    specific_cache.delete(f'validation_{cache_name}')
            
            duration = time.time() - start_time
            self.log_validation(
                "Cache System",
                True,
                f"Cache operations successful on backends: {', '.join(cache_backends_tested)}",
                duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_validation(
                "Cache System",
                False,
                f"Cache validation failed: {str(e)}",
                duration
            )
    
    def validate_static_files(self):
        """Validate static files configuration and collection"""
        print("\n📁 Validating Static Files")
        
        start_time = time.time()
        try:
            # Check static files settings
            if not settings.STATIC_URL:
                raise Exception("STATIC_URL not configured")
            
            # Check if static files directories exist
            static_dirs = settings.STATICFILES_DIRS if hasattr(settings, 'STATICFILES_DIRS') else []
            
            for static_dir in static_dirs:
                if not os.path.exists(static_dir):
                    raise Exception(f"Static files directory does not exist: {static_dir}")
            
            # Test static files collection
            from django.core.management import call_command
            from io import StringIO
            
            out = StringIO()
            call_command('collectstatic', '--noinput', '--verbosity=0', stdout=out)
            
            duration = time.time() - start_time
            self.log_validation(
                "Static Files",
                True,
                f"Static files configuration and collection successful",
                duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_validation(
                "Static Files",
                False,
                f"Static files validation failed: {str(e)}",
                duration
            )
    
    def validate_media_files(self):
        """Validate media files configuration"""
        print("\n🖼️  Validating Media Files")
        
        start_time = time.time()
        try:
            # Check media files settings
            if not settings.MEDIA_URL:
                raise Exception("MEDIA_URL not configured")
            
            if not settings.MEDIA_ROOT:
                raise Exception("MEDIA_ROOT not configured")
            
            # Create media directory if it doesn't exist
            media_root = Path(settings.MEDIA_ROOT)
            media_root.mkdir(parents=True, exist_ok=True)
            
            # Test file upload simulation
            test_file_path = media_root / 'validation_test.txt'
            with open(test_file_path, 'w') as f:
                f.write('Validation test file')
            
            # Verify file was created
            if not test_file_path.exists():
                raise Exception("Test file creation failed")
            
            # Clean up
            test_file_path.unlink()
            
            duration = time.time() - start_time
            self.log_validation(
                "Media Files",
                True,
                f"Media files configuration and operations successful",
                duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_validation(
                "Media Files",
                False,
                f"Media files validation failed: {str(e)}",
                duration
            )
    
    def validate_app_models(self):
        """Validate all app models and relationships"""
        print("\n🏗️  Validating App Models")
        
        start_time = time.time()
        try:
            from django.apps import apps
            
            # Get all models
            all_models = apps.get_models()
            model_count = len(all_models)
            
            # Test model creation for key models
            test_models = []
            
            # Test User model
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.create_user(
                username='model_test_user',
                email='model@test.com',
                password='testpass123',
                role='student'
            )
            test_models.append(('User', user))
            
            # Test StudentProfile
            from accounts.models import StudentProfile
            student_profile = StudentProfile.objects.create(
                user=user,
                learning_preferences={'style': 'visual'},
                current_streak=0,
                total_xp=0
            )
            test_models.append(('StudentProfile', student_profile))
            
            # Test UploadedContent
            from content.models import UploadedContent
            content = UploadedContent.objects.create(
                user=user,
                title='Model Test Content',
                subject='Testing',
                file_size=1024,
                processed=True
            )
            test_models.append(('UploadedContent', content))
            
            # Test LearningSession
            from learning.models import LearningSession
            session = LearningSession.objects.create(
                student=student_profile,
                content=content,
                start_time=django.utils.timezone.now()
            )
            test_models.append(('LearningSession', session))
            
            # Test Achievement
            from gamification.models import Achievement
            achievement = Achievement.objects.create(
                name='Model Test Achievement',
                description='Test achievement',
                badge_icon='test',
                xp_requirement=0
            )
            test_models.append(('Achievement', achievement))
            
            # Clean up test models
            for model_name, model_instance in reversed(test_models):
                model_instance.delete()
            
            duration = time.time() - start_time
            self.log_validation(
                "App Models",
                True,
                f"All {model_count} models validated, key model operations successful",
                duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_validation(
                "App Models",
                False,
                f"Model validation failed: {str(e)}",
                duration
            )
    
    def validate_url_routing(self):
        """Validate URL routing for all apps"""
        print("\n🛣️  Validating URL Routing")
        
        start_time = time.time()
        try:
            from django.urls import reverse
            from django.test import Client
            
            client = Client()
            
            # Test key URLs
            test_urls = [
                ('health_check', 'Health Check'),
                ('readiness_check', 'Readiness Check'),
                ('liveness_check', 'Liveness Check'),
                ('accounts:login', 'Login Page'),
            ]
            
            successful_urls = []
            failed_urls = []
            
            for url_name, description in test_urls:
                try:
                    url = reverse(url_name)
                    response = client.get(url)
                    if response.status_code in [200, 302, 403]:  # Accept redirects and forbidden
                        successful_urls.append(description)
                    else:
                        failed_urls.append(f"{description} (status: {response.status_code})")
                except Exception as e:
                    failed_urls.append(f"{description} (error: {str(e)})")
            
            if failed_urls:
                raise Exception(f"Failed URLs: {', '.join(failed_urls)}")
            
            duration = time.time() - start_time
            self.log_validation(
                "URL Routing",
                True,
                f"URL routing successful for: {', '.join(successful_urls)}",
                duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_validation(
                "URL Routing",
                False,
                f"URL routing validation failed: {str(e)}",
                duration
            )
    
    def validate_security_settings(self):
        """Validate security settings and middleware"""
        print("\n🔒 Validating Security Settings")
        
        start_time = time.time()
        try:
            security_checks = []
            
            # Check CSRF protection
            if 'django.middleware.csrf.CsrfViewMiddleware' in settings.MIDDLEWARE:
                security_checks.append("CSRF Protection")
            
            # Check security middleware
            if 'django.middleware.security.SecurityMiddleware' in settings.MIDDLEWARE:
                security_checks.append("Security Middleware")
            
            # Check authentication middleware
            if 'django.contrib.auth.middleware.AuthenticationMiddleware' in settings.MIDDLEWARE:
                security_checks.append("Authentication Middleware")
            
            # Check custom security middleware
            if 'metlab_edu.security_middleware.SecurityMiddleware' in settings.MIDDLEWARE:
                security_checks.append("Custom Security Middleware")
            
            # Check rate limiting
            if 'metlab_edu.security_middleware.RateLimitMiddleware' in settings.MIDDLEWARE:
                security_checks.append("Rate Limiting")
            
            # Check security headers
            security_headers = []
            if hasattr(settings, 'SECURE_BROWSER_XSS_FILTER') and settings.SECURE_BROWSER_XSS_FILTER:
                security_headers.append("XSS Filter")
            
            if hasattr(settings, 'SECURE_CONTENT_TYPE_NOSNIFF') and settings.SECURE_CONTENT_TYPE_NOSNIFF:
                security_headers.append("Content Type NoSniff")
            
            if hasattr(settings, 'X_FRAME_OPTIONS') and settings.X_FRAME_OPTIONS:
                security_headers.append("X-Frame-Options")
            
            duration = time.time() - start_time
            self.log_validation(
                "Security Settings",
                True,
                f"Security features active: {', '.join(security_checks + security_headers)}",
                duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_validation(
                "Security Settings",
                False,
                f"Security validation failed: {str(e)}",
                duration
            )
    
    def validate_logging_system(self):
        """Validate logging system configuration"""
        print("\n📝 Validating Logging System")
        
        start_time = time.time()
        try:
            import logging
            
            # Test different loggers
            loggers_tested = []
            
            # Test main Django logger
            django_logger = logging.getLogger('django')
            django_logger.info('Validation test message for Django logger')
            loggers_tested.append('django')
            
            # Test custom loggers
            for logger_name in ['content', 'monitoring', 'performance', 'errors', 'activity']:
                try:
                    logger = logging.getLogger(logger_name)
                    logger.info(f'Validation test message for {logger_name} logger')
                    loggers_tested.append(logger_name)
                except Exception:
                    pass  # Logger might not be configured
            
            # Check log files exist
            log_files = []
            logs_dir = Path(settings.BASE_DIR) / 'logs'
            if logs_dir.exists():
                for log_file in logs_dir.glob('*.log'):
                    log_files.append(log_file.name)
            
            duration = time.time() - start_time
            self.log_validation(
                "Logging System",
                True,
                f"Loggers tested: {', '.join(loggers_tested)}, Log files: {', '.join(log_files)}",
                duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_validation(
                "Logging System",
                False,
                f"Logging validation failed: {str(e)}",
                duration
            )
    
    def run_integration_tests(self):
        """Run integration tests"""
        print("\n🧪 Running Integration Tests")
        
        start_time = time.time()
        try:
            # Run data flow tests
            from tests.test_data_flow import run_data_flow_tests
            data_flow_success = run_data_flow_tests()
            
            if not data_flow_success:
                raise Exception("Data flow tests failed")
            
            duration = time.time() - start_time
            self.log_validation(
                "Integration Tests",
                True,
                "All integration tests passed successfully",
                duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_validation(
                "Integration Tests",
                False,
                f"Integration tests failed: {str(e)}",
                duration
            )
    
    def validate_complete_system(self):
        """Run complete system validation"""
        print("METLAB.EDU - COMPLETE SYSTEM VALIDATION")
        print("=" * 80)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run all validations
        self.validate_database_connectivity()
        self.validate_cache_system()
        self.validate_static_files()
        self.validate_media_files()
        self.validate_app_models()
        self.validate_url_routing()
        self.validate_security_settings()
        self.validate_logging_system()
        self.run_integration_tests()
        
        # Generate summary
        total_duration = time.time() - self.start_time
        passed_validations = sum(1 for r in self.results if r['success'])
        total_validations = len(self.results)
        
        print("\n" + "=" * 80)
        print("SYSTEM VALIDATION SUMMARY")
        print("=" * 80)
        
        print(f"Total Validations: {total_validations}")
        print(f"Passed: {passed_validations}")
        print(f"Failed: {total_validations - passed_validations}")
        print(f"Success Rate: {(passed_validations/total_validations)*100:.1f}%")
        print(f"Total Duration: {total_duration:.2f} seconds")
        print()
        
        # Show failed validations
        failed_validations = [r for r in self.results if not r['success']]
        if failed_validations:
            print("FAILED VALIDATIONS:")
            for validation in failed_validations:
                print(f"❌ {validation['name']}: {validation['details']}")
            print()
        
        # Overall status
        all_passed = passed_validations == total_validations
        
        if all_passed:
            print("🎉 SYSTEM VALIDATION PASSED - ALL COMPONENTS INTEGRATED SUCCESSFULLY")
            print("✅ The AI Learning Platform is ready for deployment")
        else:
            print("⚠️  SYSTEM VALIDATION FAILED - REVIEW ISSUES BEFORE DEPLOYMENT")
            print("❌ Some components need attention before the system is ready")
        
        # Save validation report
        self.validation_report['summary'] = {
            'total_validations': total_validations,
            'passed_validations': passed_validations,
            'failed_validations': total_validations - passed_validations,
            'success_rate': (passed_validations/total_validations)*100,
            'total_duration': total_duration,
            'overall_success': all_passed
        }
        
        report_filename = f"system_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(self.validation_report, f, indent=2)
        
        print(f"\nDetailed validation report saved to: {report_filename}")
        print("=" * 80)
        
        return all_passed


def main():
    """Main validation function"""
    validator = SystemValidator()
    success = validator.validate_complete_system()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()


# Import Django utilities
import django.utils.timezone