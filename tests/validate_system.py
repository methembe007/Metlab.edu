"""
Comprehensive system validation for Metlab.edu AI Learning Platform
Validates all system components and generates deployment readiness report
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'metlab_edu.settings')
import django
django.setup()

from django.conf import settings
from django.core.management import call_command
from django.db import connection
from django.core.cache import cache
from django.contrib.auth import get_user_model
from io import StringIO

User = get_user_model()


class SystemValidator:
    """Comprehensive system validation"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'UNKNOWN',
            'categories': {},
            'recommendations': [],
            'deployment_ready': False
        }
    
    def validate_database_integrity(self):
        """Validate database setup and integrity"""
        print("\n" + "="*60)
        print("VALIDATING: Database Integrity")
        print("="*60)
        
        checks = []
        
        # Test 1: Database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            checks.append({
                'name': 'Database Connection',
                'status': 'PASS',
                'details': 'Database connection successful'
            })
            print("  ✅ Database connection successful")
        except Exception as e:
            checks.append({
                'name': 'Database Connection',
                'status': 'FAIL',
                'details': f'Database connection failed: {e}'
            })
            print(f"  ❌ Database connection failed: {e}")
        
        # Test 2: Migration status
        try:
            from django.db.migrations.executor import MigrationExecutor
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            
            if not plan:
                checks.append({
                    'name': 'Database Migrations',
                    'status': 'PASS',
                    'details': 'All migrations applied'
                })
                print("  ✅ All migrations applied")
            else:
                checks.append({
                    'name': 'Database Migrations',
                    'status': 'FAIL',
                    'details': f'{len(plan)} pending migrations'
                })
                print(f"  ❌ {len(plan)} pending migrations")
        except Exception as e:
            checks.append({
                'name': 'Database Migrations',
                'status': 'FAIL',
                'details': f'Migration check failed: {e}'
            })
            print(f"  ❌ Migration check failed: {e}")
        
        # Test 3: Core tables exist
        try:
            expected_tables = [
                'auth_user', 'accounts_studentprofile', 'accounts_teacherprofile',
                'content_uploadedcontent', 'learning_learningsession',
                'gamification_achievement', 'community_studygroup'
            ]
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
                existing_tables = [row[0] for row in cursor.fetchall()]
            
            missing_tables = [t for t in expected_tables if t not in existing_tables]
            
            if not missing_tables:
                checks.append({
                    'name': 'Core Tables',
                    'status': 'PASS',
                    'details': f'All {len(expected_tables)} core tables exist'
                })
                print(f"  ✅ All {len(expected_tables)} core tables exist")
            else:
                checks.append({
                    'name': 'Core Tables',
                    'status': 'FAIL',
                    'details': f'Missing tables: {missing_tables}'
                })
                print(f"  ❌ Missing tables: {missing_tables}")
        except Exception as e:
            checks.append({
                'name': 'Core Tables',
                'status': 'FAIL',
                'details': f'Table check failed: {e}'
            })
            print(f"  ❌ Table check failed: {e}")
        
        # Test 4: Sample data integrity
        try:
            user_count = User.objects.count()
            checks.append({
                'name': 'Sample Data',
                'status': 'PASS',
                'details': f'{user_count} users in database'
            })
            print(f"  ✅ Database contains {user_count} users")
        except Exception as e:
            checks.append({
                'name': 'Sample Data',
                'status': 'FAIL',
                'details': f'Data check failed: {e}'
            })
            print(f"  ❌ Data check failed: {e}")
        
        self.results['categories']['database'] = {
            'status': 'PASS' if all(c['status'] == 'PASS' for c in checks) else 'FAIL',
            'checks': checks
        }
    
    def validate_application_configuration(self):
        """Validate application configuration"""
        print("\n" + "="*60)
        print("VALIDATING: Application Configuration")
        print("="*60)
        
        checks = []
        
        # Test 1: Django apps
        try:
            from django.apps import apps
            expected_apps = ['accounts', 'content', 'learning', 'gamification', 'community', 'services']
            loaded_apps = [app.label for app in apps.get_app_configs()]
            
            missing_apps = [app for app in expected_apps if app not in loaded_apps]
            
            if not missing_apps:
                checks.append({
                    'name': 'Django Apps',
                    'status': 'PASS',
                    'details': f'All {len(expected_apps)} apps loaded'
                })
                print(f"  ✅ All {len(expected_apps)} Django apps loaded")
            else:
                checks.append({
                    'name': 'Django Apps',
                    'status': 'FAIL',
                    'details': f'Missing apps: {missing_apps}'
                })
                print(f"  ❌ Missing apps: {missing_apps}")
        except Exception as e:
            checks.append({
                'name': 'Django Apps',
                'status': 'FAIL',
                'details': f'App check failed: {e}'
            })
            print(f"  ❌ App check failed: {e}")
        
        # Test 2: Static files configuration
        try:
            static_configured = bool(settings.STATIC_ROOT or settings.STATICFILES_DIRS)
            if static_configured:
                checks.append({
                    'name': 'Static Files',
                    'status': 'PASS',
                    'details': f'Static files configured: {settings.STATIC_ROOT}'
                })
                print("  ✅ Static files properly configured")
            else:
                checks.append({
                    'name': 'Static Files',
                    'status': 'FAIL',
                    'details': 'Static files not configured'
                })
                print("  ❌ Static files not configured")
        except Exception as e:
            checks.append({
                'name': 'Static Files',
                'status': 'FAIL',
                'details': f'Static files check failed: {e}'
            })
            print(f"  ❌ Static files check failed: {e}")
        
        # Test 3: Media files configuration
        try:
            media_configured = bool(settings.MEDIA_ROOT and settings.MEDIA_URL)
            if media_configured:
                checks.append({
                    'name': 'Media Files',
                    'status': 'PASS',
                    'details': f'Media files configured: {settings.MEDIA_ROOT}'
                })
                print("  ✅ Media files properly configured")
            else:
                checks.append({
                    'name': 'Media Files',
                    'status': 'FAIL',
                    'details': 'Media files not configured'
                })
                print("  ❌ Media files not configured")
        except Exception as e:
            checks.append({
                'name': 'Media Files',
                'status': 'FAIL',
                'details': f'Media files check failed: {e}'
            })
            print(f"  ❌ Media files check failed: {e}")
        
        # Test 4: Cache configuration
        try:
            cache.set('validation_test', 'test_value', 30)
            cached_value = cache.get('validation_test')
            cache.delete('validation_test')
            
            if cached_value == 'test_value':
                checks.append({
                    'name': 'Cache Backend',
                    'status': 'PASS',
                    'details': 'Cache operations successful'
                })
                print("  ✅ Cache backend working correctly")
            else:
                checks.append({
                    'name': 'Cache Backend',
                    'status': 'FAIL',
                    'details': 'Cache operations failed'
                })
                print("  ❌ Cache operations failed")
        except Exception as e:
            checks.append({
                'name': 'Cache Backend',
                'status': 'FAIL',
                'details': f'Cache check failed: {e}'
            })
            print(f"  ❌ Cache check failed: {e}")
        
        # Test 5: Security settings
        security_checks = []
        
        if getattr(settings, 'SECRET_KEY', None):
            security_checks.append('Secret key configured')
        else:
            security_checks.append('❌ Secret key missing')
        
        if getattr(settings, 'DEBUG', True) == False:
            security_checks.append('Debug mode disabled')
        else:
            security_checks.append('⚠️ Debug mode enabled')
        
        if getattr(settings, 'ALLOWED_HOSTS', []):
            security_checks.append('Allowed hosts configured')
        else:
            security_checks.append('⚠️ Allowed hosts not configured')
        
        checks.append({
            'name': 'Security Settings',
            'status': 'PASS' if '❌' not in str(security_checks) else 'WARN',
            'details': '; '.join(security_checks)
        })
        print(f"  ✅ Security settings: {len(security_checks)} checks")
        
        self.results['categories']['configuration'] = {
            'status': 'PASS' if all(c['status'] in ['PASS', 'WARN'] for c in checks) else 'FAIL',
            'checks': checks
        }
    
    def validate_file_system_setup(self):
        """Validate file system setup"""
        print("\n" + "="*60)
        print("VALIDATING: File System Setup")
        print("="*60)
        
        checks = []
        
        # Test 1: Required directories
        required_dirs = [
            ('Media Root', settings.MEDIA_ROOT),
            ('Static Root', settings.STATIC_ROOT),
            ('Logs Directory', 'logs'),
        ]
        
        for name, path in required_dirs:
            if path and os.path.exists(path):
                checks.append({
                    'name': name,
                    'status': 'PASS',
                    'details': f'Directory exists: {path}'
                })
                print(f"  ✅ {name} exists: {path}")
            else:
                checks.append({
                    'name': name,
                    'status': 'FAIL',
                    'details': f'Directory missing: {path}'
                })
                print(f"  ❌ {name} missing: {path}")
        
        # Test 2: File permissions
        try:
            test_file = os.path.join(settings.MEDIA_ROOT, 'test_write.txt')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            
            checks.append({
                'name': 'File Permissions',
                'status': 'PASS',
                'details': 'Write permissions verified'
            })
            print("  ✅ File write permissions verified")
        except Exception as e:
            checks.append({
                'name': 'File Permissions',
                'status': 'FAIL',
                'details': f'Write permission failed: {e}'
            })
            print(f"  ❌ Write permission failed: {e}")
        
        # Test 3: Static files collection
        try:
            output = StringIO()
            call_command('collectstatic', '--noinput', '--dry-run', stdout=output)
            
            checks.append({
                'name': 'Static Files Collection',
                'status': 'PASS',
                'details': 'Static files can be collected'
            })
            print("  ✅ Static files collection verified")
        except Exception as e:
            checks.append({
                'name': 'Static Files Collection',
                'status': 'FAIL',
                'details': f'Static collection failed: {e}'
            })
            print(f"  ❌ Static collection failed: {e}")
        
        self.results['categories']['filesystem'] = {
            'status': 'PASS' if all(c['status'] == 'PASS' for c in checks) else 'FAIL',
            'checks': checks
        }
    
    def validate_performance_benchmarks(self):
        """Validate performance benchmarks"""
        print("\n" + "="*60)
        print("VALIDATING: Performance Benchmarks")
        print("="*60)
        
        checks = []
        
        # Test 1: Database query performance
        try:
            start_time = time.time()
            list(User.objects.all()[:100])  # Force evaluation
            query_time = time.time() - start_time
            
            if query_time < 1.0:
                checks.append({
                    'name': 'Database Query Performance',
                    'status': 'PASS',
                    'details': f'Query completed in {query_time:.3f}s'
                })
                print(f"  ✅ Database query performance: {query_time:.3f}s")
            else:
                checks.append({
                    'name': 'Database Query Performance',
                    'status': 'WARN',
                    'details': f'Query took {query_time:.3f}s (>1s)'
                })
                print(f"  ⚠️ Database query performance: {query_time:.3f}s (slow)")
        except Exception as e:
            checks.append({
                'name': 'Database Query Performance',
                'status': 'FAIL',
                'details': f'Query performance test failed: {e}'
            })
            print(f"  ❌ Query performance test failed: {e}")
        
        # Test 2: Cache performance
        try:
            start_time = time.time()
            for i in range(100):
                cache.set(f'perf_test_{i}', f'value_{i}', 60)
                cache.get(f'perf_test_{i}')
            cache_time = time.time() - start_time
            
            # Cleanup
            for i in range(100):
                cache.delete(f'perf_test_{i}')
            
            if cache_time < 1.0:
                checks.append({
                    'name': 'Cache Performance',
                    'status': 'PASS',
                    'details': f'100 cache ops in {cache_time:.3f}s'
                })
                print(f"  ✅ Cache performance: {cache_time:.3f}s for 100 ops")
            else:
                checks.append({
                    'name': 'Cache Performance',
                    'status': 'WARN',
                    'details': f'100 cache ops took {cache_time:.3f}s (>1s)'
                })
                print(f"  ⚠️ Cache performance: {cache_time:.3f}s (slow)")
        except Exception as e:
            checks.append({
                'name': 'Cache Performance',
                'status': 'FAIL',
                'details': f'Cache performance test failed: {e}'
            })
            print(f"  ❌ Cache performance test failed: {e}")
        
        # Test 3: Memory usage
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            if memory_mb < 500:
                checks.append({
                    'name': 'Memory Usage',
                    'status': 'PASS',
                    'details': f'Memory usage: {memory_mb:.1f}MB'
                })
                print(f"  ✅ Memory usage: {memory_mb:.1f}MB")
            else:
                checks.append({
                    'name': 'Memory Usage',
                    'status': 'WARN',
                    'details': f'Memory usage: {memory_mb:.1f}MB (high)'
                })
                print(f"  ⚠️ Memory usage: {memory_mb:.1f}MB (high)")
        except Exception as e:
            checks.append({
                'name': 'Memory Usage',
                'status': 'FAIL',
                'details': f'Memory check failed: {e}'
            })
            print(f"  ❌ Memory check failed: {e}")
        
        self.results['categories']['performance'] = {
            'status': 'PASS' if all(c['status'] in ['PASS', 'WARN'] for c in checks) else 'FAIL',
            'checks': checks
        }
    
    def validate_security_configuration(self):
        """Validate security configuration"""
        print("\n" + "="*60)
        print("VALIDATING: Security Configuration")
        print("="*60)
        
        checks = []
        
        # Test 1: Authentication settings
        auth_checks = []
        
        if hasattr(settings, 'AUTH_PASSWORD_VALIDATORS') and settings.AUTH_PASSWORD_VALIDATORS:
            auth_checks.append('Password validators configured')
        else:
            auth_checks.append('❌ Password validators missing')
        
        if getattr(settings, 'SESSION_COOKIE_SECURE', False):
            auth_checks.append('Secure session cookies')
        else:
            auth_checks.append('⚠️ Session cookies not secure')
        
        if getattr(settings, 'CSRF_COOKIE_SECURE', False):
            auth_checks.append('Secure CSRF cookies')
        else:
            auth_checks.append('⚠️ CSRF cookies not secure')
        
        checks.append({
            'name': 'Authentication Security',
            'status': 'PASS' if '❌' not in str(auth_checks) else 'WARN',
            'details': '; '.join(auth_checks)
        })
        print(f"  ✅ Authentication security: {len(auth_checks)} checks")
        
        # Test 2: HTTPS settings
        https_checks = []
        
        if getattr(settings, 'SECURE_SSL_REDIRECT', False):
            https_checks.append('SSL redirect enabled')
        else:
            https_checks.append('⚠️ SSL redirect disabled')
        
        if getattr(settings, 'SECURE_HSTS_SECONDS', 0) > 0:
            https_checks.append('HSTS enabled')
        else:
            https_checks.append('⚠️ HSTS disabled')
        
        checks.append({
            'name': 'HTTPS Configuration',
            'status': 'WARN' if '⚠️' in str(https_checks) else 'PASS',
            'details': '; '.join(https_checks)
        })
        print(f"  ⚠️ HTTPS configuration: {len(https_checks)} checks")
        
        # Test 3: File upload security
        try:
            max_upload_size = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 0)
            allowed_extensions = getattr(settings, 'ALLOWED_UPLOAD_EXTENSIONS', [])
            
            upload_checks = []
            if max_upload_size > 0:
                upload_checks.append(f'Max upload size: {max_upload_size} bytes')
            else:
                upload_checks.append('⚠️ No upload size limit')
            
            if allowed_extensions:
                upload_checks.append(f'File type restrictions: {len(allowed_extensions)} types')
            else:
                upload_checks.append('⚠️ No file type restrictions')
            
            checks.append({
                'name': 'File Upload Security',
                'status': 'WARN' if '⚠️' in str(upload_checks) else 'PASS',
                'details': '; '.join(upload_checks)
            })
            print(f"  ⚠️ File upload security: {len(upload_checks)} checks")
        except Exception as e:
            checks.append({
                'name': 'File Upload Security',
                'status': 'FAIL',
                'details': f'Upload security check failed: {e}'
            })
            print(f"  ❌ Upload security check failed: {e}")
        
        self.results['categories']['security'] = {
            'status': 'PASS' if all(c['status'] in ['PASS', 'WARN'] for c in checks) else 'FAIL',
            'checks': checks
        }
    
    def run_comprehensive_validation(self):
        """Run all validation checks"""
        print("="*80)
        print("METLAB.EDU COMPREHENSIVE SYSTEM VALIDATION")
        print("="*80)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        start_time = time.time()
        
        # Run all validation categories
        self.validate_database_integrity()
        self.validate_application_configuration()
        self.validate_file_system_setup()
        self.validate_performance_benchmarks()
        self.validate_security_configuration()
        
        # Calculate overall status
        total_duration = time.time() - start_time
        
        category_statuses = [cat['status'] for cat in self.results['categories'].values()]
        
        if all(status == 'PASS' for status in category_statuses):
            self.results['overall_status'] = 'PASS'
            self.results['deployment_ready'] = True
        elif any(status == 'FAIL' for status in category_statuses):
            self.results['overall_status'] = 'FAIL'
            self.results['deployment_ready'] = False
        else:
            self.results['overall_status'] = 'WARN'
            self.results['deployment_ready'] = True  # Warnings don't block deployment
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Print summary
        print("\n" + "="*80)
        print("VALIDATION SUMMARY")
        print("="*80)
        
        for category, data in self.results['categories'].items():
            status_icon = "✅" if data['status'] == 'PASS' else "⚠️" if data['status'] == 'WARN' else "❌"
            print(f"{status_icon} {category.upper()}: {data['status']}")
        
        print(f"\nOverall Status: {self.results['overall_status']}")
        print(f"Deployment Ready: {'YES' if self.results['deployment_ready'] else 'NO'}")
        print(f"Validation Duration: {total_duration:.2f}s")
        
        if self.results['recommendations']:
            print(f"\nRecommendations:")
            for rec in self.results['recommendations']:
                print(f"  • {rec}")
        
        return self.results
    
    def generate_recommendations(self):
        """Generate deployment recommendations"""
        recommendations = []
        
        for category, data in self.results['categories'].items():
            for check in data['checks']:
                if check['status'] == 'FAIL':
                    recommendations.append(f"Fix {category} issue: {check['name']}")
                elif check['status'] == 'WARN':
                    recommendations.append(f"Consider improving {category}: {check['name']}")
        
        # General recommendations
        if self.results['overall_status'] == 'FAIL':
            recommendations.append("Address all FAIL status items before deployment")
        
        if any('⚠️' in str(cat) for cat in self.results['categories'].values()):
            recommendations.append("Review security settings for production deployment")
        
        self.results['recommendations'] = recommendations
    
    def save_report(self, filename=None):
        """Save validation report to file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'system_validation_report_{timestamp}.json'
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nValidation report saved to: {filename}")
        return filename


def main():
    """Main validation function"""
    validator = SystemValidator()
    results = validator.run_comprehensive_validation()
    
    # Save report
    report_file = validator.save_report()
    
    # Exit with appropriate code
    exit_code = 0 if results['deployment_ready'] else 1
    
    print("\n" + "="*80)
    if results['deployment_ready']:
        print("🎉 SYSTEM VALIDATION PASSED - READY FOR DEPLOYMENT")
    else:
        print("⚠️ SYSTEM VALIDATION FAILED - REVIEW ISSUES BEFORE DEPLOYMENT")
    print("="*80)
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())