#!/usr/bin/env python
"""
Test script to verify all teacher URLs are working
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'metlab_edu.settings')
django.setup()

from django.urls import reverse, NoReverseMatch

def test_url_resolution():
    """Test that all learning URLs can be resolved"""
    
    print("Testing URL Resolution...")
    print("=" * 60)
    
    # URLs without parameters
    simple_urls = [
        'learning:teacher_content_dashboard',
        'learning:upload_content',
        'learning:teacher_content_list',
        'learning:class_management',
        'learning:create_class',
        'learning:teacher_quiz_list',
        'learning:bulk_assign_content',
        'learning:enroll_in_class',
    ]
    
    # URLs with parameters (using dummy IDs)
    param_urls = [
        ('learning:class_detail', [1]),
        ('learning:student_progress', [1]),
        ('learning:class_analytics', [1]),
        ('learning:teacher_content_detail', [1]),
        ('learning:customize_quiz', [1]),
    ]
    
    passed = 0
    failed = 0
    
    # Test simple URLs
    print("\nSimple URLs:")
    for url_name in simple_urls:
        try:
            url = reverse(url_name)
            print(f"  ✓ {url_name:40} -> {url}")
            passed += 1
        except NoReverseMatch as e:
            print(f"  ✗ {url_name:40} -> ERROR: {e}")
            failed += 1
    
    # Test parameterized URLs
    print("\nParameterized URLs:")
    for url_name, args in param_urls:
        try:
            url = reverse(url_name, args=args)
            print(f"  ✓ {url_name:40} -> {url}")
            passed += 1
        except NoReverseMatch as e:
            print(f"  ✗ {url_name:40} -> ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    
    return failed == 0

if __name__ == '__main__':
    success = test_url_resolution()
    
    if success:
        print("\n✓ All URLs resolved successfully!")
        print("The teacher upload page should now work correctly.")
    else:
        print("\n✗ Some URLs failed to resolve.")
        print("Please check the URL configuration.")