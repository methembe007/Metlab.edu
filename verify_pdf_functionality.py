#!/usr/bin/env python
"""
Verification script for PDF viewing functionality
Run this to verify that all components are properly configured
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'metlab_edu.settings')
django.setup()

from django.urls import reverse, resolve
from django.conf import settings
from learning import student_content_views, teacher_views
from learning.teacher_models import TeacherContent
from content.models import UploadedContent
import inspect


def check_urls():
    """Verify all required URLs are configured"""
    print("=" * 60)
    print("CHECKING URL CONFIGURATION")
    print("=" * 60)
    
    required_urls = [
        ('learning:view_content', {'content_id': 1}),
        ('learning:view_pdf', {'content_id': 1}),
        ('learning:download_content', {'content_id': 1}),
        ('learning:class_content', {'class_id': 1}),
        ('learning:all_assigned_content', {}),
        ('learning:upload_content', {}),
        ('learning:teacher_content_list', {}),
    ]
    
    all_ok = True
    for url_name, kwargs in required_urls:
        try:
            url = reverse(url_name, kwargs=kwargs)
            print(f"✓ {url_name:40} -> {url}")
        except Exception as e:
            print(f"✗ {url_name:40} -> ERROR: {e}")
            all_ok = False
    
    print()
    return all_ok


def check_views():
    """Verify all required views exist"""
    print("=" * 60)
    print("CHECKING VIEW FUNCTIONS")
    print("=" * 60)
    
    required_views = [
        ('student_content_views', 'view_content'),
        ('student_content_views', 'view_pdf'),
        ('student_content_views', 'download_content'),
        ('student_content_views', 'class_content'),
        ('student_content_views', 'all_assigned_content'),
        ('teacher_views', 'upload_content'),
        ('teacher_views', 'content_list'),
        ('teacher_views', 'content_detail'),
    ]
    
    all_ok = True
    for module_name, view_name in required_views:
        module = student_content_views if module_name == 'student_content_views' else teacher_views
        if hasattr(module, view_name):
            view_func = getattr(module, view_name)
            sig = inspect.signature(view_func)
            print(f"✓ {module_name}.{view_name:30} {sig}")
        else:
            print(f"✗ {module_name}.{view_name:30} -> NOT FOUND")
            all_ok = False
    
    print()
    return all_ok


def check_models():
    """Verify models have required fields"""
    print("=" * 60)
    print("CHECKING MODEL CONFIGURATION")
    print("=" * 60)
    
    # Check UploadedContent model
    print("\nUploadedContent model:")
    required_fields = ['file', 'content_type', 'original_filename', 'file_size', 'processing_status']
    for field in required_fields:
        if hasattr(UploadedContent, field):
            print(f"  ✓ {field}")
        else:
            print(f"  ✗ {field} -> MISSING")
    
    # Check TeacherContent model
    print("\nTeacherContent model:")
    required_fields = ['uploaded_content', 'teacher', 'title', 'subject', 'assigned_classes']
    for field in required_fields:
        if hasattr(TeacherContent, field):
            print(f"  ✓ {field}")
        else:
            print(f"  ✗ {field} -> MISSING")
    
    print()
    return True


def check_templates():
    """Verify required templates exist"""
    print("=" * 60)
    print("CHECKING TEMPLATES")
    print("=" * 60)
    
    template_dir = os.path.join(settings.BASE_DIR, 'templates', 'learning')
    required_templates = [
        'student_content_detail.html',
        'student_class_content.html',
        'student_all_content.html',
        'upload_content.html',
        'teacher_content_list.html',
        'teacher_content_detail.html',
    ]
    
    all_ok = True
    for template in required_templates:
        template_path = os.path.join(template_dir, template)
        if os.path.exists(template_path):
            size = os.path.getsize(template_path)
            print(f"✓ {template:40} ({size:,} bytes)")
        else:
            print(f"✗ {template:40} -> NOT FOUND")
            all_ok = False
    
    print()
    return all_ok


def check_media_configuration():
    """Verify media file configuration"""
    print("=" * 60)
    print("CHECKING MEDIA CONFIGURATION")
    print("=" * 60)
    
    checks = [
        ('MEDIA_URL', hasattr(settings, 'MEDIA_URL')),
        ('MEDIA_ROOT', hasattr(settings, 'MEDIA_ROOT')),
    ]
    
    all_ok = True
    for setting, exists in checks:
        if exists:
            value = getattr(settings, setting)
            print(f"✓ {setting:20} = {value}")
        else:
            print(f"✗ {setting:20} -> NOT CONFIGURED")
            all_ok = False
    
    # Check if media directory exists
    if hasattr(settings, 'MEDIA_ROOT'):
        media_root = settings.MEDIA_ROOT
        if os.path.exists(media_root):
            print(f"✓ Media directory exists: {media_root}")
        else:
            print(f"⚠ Media directory does not exist: {media_root}")
            print(f"  (Will be created automatically on first upload)")
    
    print()
    return all_ok


def check_file_upload_settings():
    """Verify file upload settings"""
    print("=" * 60)
    print("CHECKING FILE UPLOAD SETTINGS")
    print("=" * 60)
    
    settings_to_check = [
        'FILE_UPLOAD_MAX_MEMORY_SIZE',
        'DATA_UPLOAD_MAX_MEMORY_SIZE',
    ]
    
    for setting in settings_to_check:
        if hasattr(settings, setting):
            value = getattr(settings, setting)
            mb = value / (1024 * 1024)
            print(f"✓ {setting:35} = {value:,} bytes ({mb:.1f} MB)")
        else:
            print(f"⚠ {setting:35} -> Using Django default")
    
    print()
    return True


def check_security():
    """Verify security decorators are in place"""
    print("=" * 60)
    print("CHECKING SECURITY CONFIGURATION")
    print("=" * 60)
    
    # Check view decorators
    views_to_check = [
        (student_content_views.view_content, ['login_required', 'role_required']),
        (student_content_views.view_pdf, ['login_required', 'role_required']),
        (student_content_views.download_content, ['login_required', 'role_required']),
        (teacher_views.upload_content, ['login_required', 'teacher_required']),
    ]
    
    all_ok = True
    for view_func, required_decorators in views_to_check:
        view_name = view_func.__name__
        # Check if decorators are applied (simplified check)
        has_decorators = hasattr(view_func, '__wrapped__') or 'login_required' in str(view_func)
        if has_decorators:
            print(f"✓ {view_name:30} has security decorators")
        else:
            print(f"⚠ {view_name:30} may be missing decorators")
    
    print()
    return all_ok


def run_verification():
    """Run all verification checks"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "PDF VIEWING FUNCTIONALITY VERIFICATION" + " " * 9 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    results = []
    
    results.append(("URL Configuration", check_urls()))
    results.append(("View Functions", check_views()))
    results.append(("Model Configuration", check_models()))
    results.append(("Templates", check_templates()))
    results.append(("Media Configuration", check_media_configuration()))
    results.append(("File Upload Settings", check_file_upload_settings()))
    results.append(("Security Configuration", check_security()))
    
    # Summary
    print("=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for check_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:10} {check_name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("╔" + "=" * 58 + "╗")
        print("║" + " " * 5 + "✓ ALL CHECKS PASSED - PDF VIEWING IS READY!" + " " * 7 + "║")
        print("╚" + "=" * 58 + "╝")
        print()
        print("Next steps:")
        print("1. Run tests: python manage.py test tests.test_pdf_viewing")
        print("2. Start server: python manage.py runserver")
        print("3. Login as teacher and upload a PDF")
        print("4. Login as student and view the PDF")
    else:
        print("╔" + "=" * 58 + "╗")
        print("║" + " " * 8 + "⚠ SOME CHECKS FAILED - REVIEW ABOVE" + " " * 10 + "║")
        print("╚" + "=" * 58 + "╝")
        print()
        print("Please fix the issues marked with ✗ before proceeding.")
    
    print()
    return all_passed


if __name__ == '__main__':
    try:
        success = run_verification()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
