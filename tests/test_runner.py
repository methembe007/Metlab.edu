"""
Test runner for comprehensive system integration testing.
Runs all integration tests and generates a detailed report.
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner
from django.core.management import execute_from_command_line
import subprocess
import time
from datetime import datetime


def setup_django():
    """Setup Django environment for testing"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'metlab_edu.settings')
    django.setup()


def run_integration_tests():
    """Run all integration tests and return results"""
    print("=" * 80)
    print("METLAB.EDU - COMPREHENSIVE INTEGRATION TEST SUITE")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Setup test environment
    setup_django()
    
    # Test categories to run
    test_categories = [
        {
            'name': 'Database Migrations',
            'command': ['python', 'manage.py', 'migrate', '--run-syncdb'],
            'description': 'Verify all database migrations apply correctly'
        },
        {
            'name': 'Static Files Collection',
            'command': ['python', 'manage.py', 'collectstatic', '--noinput'],
            'description': 'Verify static files can be collected'
        },
        {
            'name': 'System Health Checks',
            'command': ['python', 'manage.py', 'check'],
            'description': 'Run Django system checks'
        },
        {
            'name': 'Integration Tests',
            'command': ['python', 'manage.py', 'test', 'tests.test_integration', '-v', '2'],
            'description': 'Run comprehensive integration tests'
        },
        {
            'name': 'Individual App Tests',
            'command': ['python', 'manage.py', 'test', 'accounts', 'content', 'learning', 'gamification', 'community', '-v', '2'],
            'description': 'Run all individual app tests'
        }
    ]
    
    results = []
    total_start_time = time.time()
    
    for category in test_categories:
        print(f"Running: {category['name']}")
        print(f"Description: {category['description']}")
        print(f"Command: {' '.join(category['command'])}")
        print("-" * 60)
        
        start_time = time.time()
        try:
            result = subprocess.run(
                category['command'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            success = result.returncode == 0
            
            results.append({
                'name': category['name'],
                'success': success,
                'duration': duration,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            })
            
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"Status: {status}")
            print(f"Duration: {duration:.2f} seconds")
            
            if not success:
                print("STDERR:")
                print(result.stderr)
                print("STDOUT:")
                print(result.stdout)
            
        except subprocess.TimeoutExpired:
            results.append({
                'name': category['name'],
                'success': False,
                'duration': 300,
                'stdout': '',
                'stderr': 'Test timed out after 5 minutes',
                'returncode': -1
            })
            print("❌ FAILED - Timeout")
        
        except Exception as e:
            results.append({
                'name': category['name'],
                'success': False,
                'duration': 0,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1
            })
            print(f"❌ FAILED - Exception: {e}")
        
        print()
    
    total_duration = time.time() - total_start_time
    
    # Generate summary report
    print("=" * 80)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 80)
    
    passed_tests = sum(1 for r in results if r['success'])
    total_tests = len(results)
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print(f"Total Duration: {total_duration:.2f} seconds")
    print()
    
    # Detailed results
    for result in results:
        status = "✅ PASSED" if result['success'] else "❌ FAILED"
        print(f"{status} {result['name']} ({result['duration']:.2f}s)")
        if not result['success'] and result['stderr']:
            print(f"   Error: {result['stderr'][:100]}...")
    
    print()
    print("=" * 80)
    
    return results, passed_tests == total_tests


def verify_system_components():
    """Verify all system components are properly integrated"""
    print("SYSTEM COMPONENT VERIFICATION")
    print("=" * 80)
    
    components = []
    
    # Check Django apps are installed
    from django.apps import apps
    expected_apps = ['accounts', 'content', 'learning', 'gamification', 'community', 'services']
    
    for app_name in expected_apps:
        try:
            app = apps.get_app_config(app_name)
            components.append({
                'name': f'Django App: {app_name}',
                'status': True,
                'details': f'App loaded successfully: {app.verbose_name}'
            })
        except Exception as e:
            components.append({
                'name': f'Django App: {app_name}',
                'status': False,
                'details': f'Failed to load: {e}'
            })
    
    # Check database connectivity
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        components.append({
            'name': 'Database Connection',
            'status': True,
            'details': 'Database connection successful'
        })
    except Exception as e:
        components.append({
            'name': 'Database Connection',
            'status': False,
            'details': f'Database connection failed: {e}'
        })
    
    # Check cache backend
    try:
        from django.core.cache import cache
        cache.set('test_key', 'test_value', 30)
        value = cache.get('test_key')
        cache.delete('test_key')
        components.append({
            'name': 'Cache Backend',
            'status': value == 'test_value',
            'details': 'Cache operations successful' if value == 'test_value' else 'Cache operations failed'
        })
    except Exception as e:
        components.append({
            'name': 'Cache Backend',
            'status': False,
            'details': f'Cache backend failed: {e}'
        })
    
    # Check static files configuration
    try:
        static_root = settings.STATIC_ROOT or settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else None
        components.append({
            'name': 'Static Files Configuration',
            'status': static_root is not None,
            'details': f'Static files configured: {static_root}' if static_root else 'Static files not configured'
        })
    except Exception as e:
        components.append({
            'name': 'Static Files Configuration',
            'status': False,
            'details': f'Static files configuration error: {e}'
        })
    
    # Check media files configuration
    try:
        media_root = settings.MEDIA_ROOT
        components.append({
            'name': 'Media Files Configuration',
            'status': media_root is not None,
            'details': f'Media files configured: {media_root}' if media_root else 'Media files not configured'
        })
    except Exception as e:
        components.append({
            'name': 'Media Files Configuration',
            'status': False,
            'details': f'Media files configuration error: {e}'
        })
    
    # Check logging configuration
    try:
        import logging
        logger = logging.getLogger('django')
        logger.info('Test log message')
        components.append({
            'name': 'Logging Configuration',
            'status': True,
            'details': 'Logging system operational'
        })
    except Exception as e:
        components.append({
            'name': 'Logging Configuration',
            'status': False,
            'details': f'Logging configuration error: {e}'
        })
    
    # Print component status
    for component in components:
        status = "✅ OK" if component['status'] else "❌ FAIL"
        print(f"{status} {component['name']}")
        print(f"   {component['details']}")
    
    print()
    
    passed_components = sum(1 for c in components if c['status'])
    total_components = len(components)
    
    print(f"Component Status: {passed_components}/{total_components} OK")
    print("=" * 80)
    
    return components, passed_components == total_components


def generate_test_report(test_results, component_results):
    """Generate a comprehensive test report"""
    report_filename = f"integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(report_filename, 'w') as f:
        f.write("METLAB.EDU INTEGRATION TEST REPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Test Results
        f.write("TEST RESULTS\n")
        f.write("-" * 40 + "\n")
        for result in test_results:
            status = "PASSED" if result['success'] else "FAILED"
            f.write(f"{status}: {result['name']} ({result['duration']:.2f}s)\n")
            if not result['success']:
                f.write(f"  Error: {result['stderr']}\n")
        f.write("\n")
        
        # Component Results
        f.write("COMPONENT VERIFICATION\n")
        f.write("-" * 40 + "\n")
        for component in component_results:
            status = "OK" if component['status'] else "FAIL"
            f.write(f"{status}: {component['name']}\n")
            f.write(f"  {component['details']}\n")
        f.write("\n")
        
        # Summary
        passed_tests = sum(1 for r in test_results if r['success'])
        total_tests = len(test_results)
        passed_components = sum(1 for c in component_results if c['status'])
        total_components = len(component_results)
        
        f.write("SUMMARY\n")
        f.write("-" * 40 + "\n")
        f.write(f"Tests: {passed_tests}/{total_tests} passed\n")
        f.write(f"Components: {passed_components}/{total_components} OK\n")
        f.write(f"Overall Status: {'PASS' if passed_tests == total_tests and passed_components == total_components else 'FAIL'}\n")
    
    print(f"Detailed report saved to: {report_filename}")
    return report_filename


if __name__ == '__main__':
    # Run comprehensive integration tests
    test_results, tests_passed = run_integration_tests()
    
    # Verify system components
    component_results, components_ok = verify_system_components()
    
    # Generate report
    report_file = generate_test_report(test_results, component_results)
    
    # Final status
    overall_success = tests_passed and components_ok
    
    print("\nFINAL STATUS")
    print("=" * 80)
    if overall_success:
        print("🎉 ALL INTEGRATION TESTS PASSED - SYSTEM READY FOR DEPLOYMENT")
    else:
        print("⚠️  INTEGRATION TESTS FAILED - REVIEW ISSUES BEFORE DEPLOYMENT")
    
    print(f"Report saved to: {report_file}")
    
    # Exit with appropriate code
    sys.exit(0 if overall_success else 1)