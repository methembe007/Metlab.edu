"""
System Integration Test for AI Learning Platform
Tests complete user workflows and system integration
"""

import os
import django
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'metlab_edu.settings')
django.setup()

from accounts.models import StudentProfile, TeacherProfile, ParentProfile
from content.models import UploadedContent
from learning.models import LearningSession, DailyLesson
from gamification.models import Achievement, VirtualCurrency
from community.models import StudyGroup

User = get_user_model()


def test_student_workflow():
    """Test complete student workflow"""
    print("\n🎓 Testing Student Workflow")
    
    client = Client()
    
    # 1. Create student user
    student_user = User.objects.create_user(
        username='test_student',
        email='student@test.com',
        password='testpass123',
        role='student'
    )
    student_profile = StudentProfile.objects.create(
        user=student_user,
        learning_preferences={'style': 'visual'},
        current_streak=0,
        total_xp=0
    )
    
    print("✅ Student user created")
    
    # 2. Test login
    login_response = client.post(reverse('accounts:login'), {
        'username': 'test_student',
        'password': 'testpass123'
    })
    
    if login_response.status_code == 302:
        print("✅ Student login successful")
    else:
        print(f"❌ Student login failed: {login_response.status_code}")
        return False
    
    # 3. Access dashboard
    dashboard_response = client.get(reverse('accounts:student_dashboard'))
    if dashboard_response.status_code == 200:
        print("✅ Student dashboard accessible")
    else:
        print(f"❌ Student dashboard failed: {dashboard_response.status_code}")
        return False
    
    # 4. Test content upload (with mocked AI)
    with patch('content.ai_services.extract_key_concepts') as mock_extract:
        mock_extract.return_value = ['test', 'concept']
        
        test_file = SimpleUploadedFile(
            "test.pdf",
            b"Test PDF content",
            content_type="application/pdf"
        )
        
        upload_response = client.post(reverse('content:upload'), {
            'title': 'Test Document',
            'file': test_file,
            'subject': 'Mathematics'
        })
        
        if upload_response.status_code == 302:
            print("✅ Content upload successful")
        else:
            print(f"❌ Content upload failed: {upload_response.status_code}")
            return False
    
    # 5. Check content library
    library_response = client.get(reverse('content:library'))
    if library_response.status_code == 200:
        print("✅ Content library accessible")
    else:
        print(f"❌ Content library failed: {library_response.status_code}")
        return False
    
    # 6. Check gamification features
    achievements_response = client.get(reverse('gamification:achievements'))
    if achievements_response.status_code == 200:
        print("✅ Gamification features accessible")
    else:
        print(f"❌ Gamification failed: {achievements_response.status_code}")
        return False
    
    print("🎉 Student workflow completed successfully")
    return True


def test_teacher_workflow():
    """Test complete teacher workflow"""
    print("\n👨‍🏫 Testing Teacher Workflow")
    
    client = Client()
    
    # 1. Create teacher user
    teacher_user = User.objects.create_user(
        username='test_teacher',
        email='teacher@test.com',
        password='testpass123',
        role='teacher'
    )
    teacher_profile = TeacherProfile.objects.create(
        user=teacher_user,
        institution='Test School'
    )
    
    print("✅ Teacher user created")
    
    # 2. Test login
    login_response = client.post(reverse('accounts:login'), {
        'username': 'test_teacher',
        'password': 'testpass123'
    })
    
    if login_response.status_code == 302:
        print("✅ Teacher login successful")
    else:
        print(f"❌ Teacher login failed: {login_response.status_code}")
        return False
    
    # 3. Access teacher dashboard
    dashboard_response = client.get(reverse('accounts:teacher_dashboard'))
    if dashboard_response.status_code == 200:
        print("✅ Teacher dashboard accessible")
    else:
        print(f"❌ Teacher dashboard failed: {dashboard_response.status_code}")
        return False
    
    # 4. Check teacher content upload
    upload_response = client.get(reverse('learning:upload_content'))
    if upload_response.status_code == 200:
        print("✅ Teacher content upload accessible")
    else:
        print(f"❌ Teacher content upload failed: {upload_response.status_code}")
        return False
    
    # 5. Check teacher analytics
    analytics_response = client.get(reverse('learning:teacher_analytics'))
    if analytics_response.status_code == 200:
        print("✅ Teacher analytics accessible")
    else:
        print(f"❌ Teacher analytics failed: {analytics_response.status_code}")
        return False
    
    print("🎉 Teacher workflow completed successfully")
    return True


def test_parent_workflow():
    """Test parent workflow"""
    print("\n👨‍👩‍👧‍👦 Testing Parent Workflow")
    
    client = Client()
    
    # 1. Create parent user
    parent_user = User.objects.create_user(
        username='test_parent',
        email='parent@test.com',
        password='testpass123',
        role='parent'
    )
    parent_profile = ParentProfile.objects.create(user=parent_user)
    
    # Create child for parent
    child_user = User.objects.create_user(
        username='test_child',
        email='child@test.com',
        password='testpass123',
        role='student'
    )
    child_profile = StudentProfile.objects.create(
        user=child_user,
        learning_preferences={'style': 'visual'},
        current_streak=0,
        total_xp=0
    )
    parent_profile.children.add(child_profile)
    
    print("✅ Parent and child users created")
    
    # 2. Test login
    login_response = client.post(reverse('accounts:login'), {
        'username': 'test_parent',
        'password': 'testpass123'
    })
    
    if login_response.status_code == 302:
        print("✅ Parent login successful")
    else:
        print(f"❌ Parent login failed: {login_response.status_code}")
        return False
    
    # 3. Access parent dashboard
    dashboard_response = client.get(reverse('learning:parent_dashboard'))
    if dashboard_response.status_code == 200:
        print("✅ Parent dashboard accessible")
    else:
        print(f"❌ Parent dashboard failed: {dashboard_response.status_code}")
        return False
    
    print("🎉 Parent workflow completed successfully")
    return True


def test_system_health():
    """Test system health endpoints"""
    print("\n🏥 Testing System Health")
    
    client = Client()
    
    # Test health check endpoints
    health_endpoints = [
        ('health_check', 'Health Check'),
        ('readiness_check', 'Readiness Check'),
        ('liveness_check', 'Liveness Check'),
        ('metrics', 'Metrics')
    ]
    
    for endpoint, name in health_endpoints:
        try:
            response = client.get(reverse(endpoint))
            if response.status_code == 200:
                print(f"✅ {name} endpoint working")
            else:
                print(f"❌ {name} endpoint failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ {name} endpoint error: {e}")
            return False
    
    print("🎉 System health checks completed successfully")
    return True


def test_database_operations():
    """Test database operations"""
    print("\n🗄️ Testing Database Operations")
    
    try:
        # Test user creation
        test_user = User.objects.create_user(
            username='db_test_user',
            email='dbtest@test.com',
            password='testpass123',
            role='student'
        )
        print("✅ User creation successful")
        
        # Test profile creation
        profile = StudentProfile.objects.create(
            user=test_user,
            learning_preferences={'test': 'data'},
            current_streak=5,
            total_xp=100
        )
        print("✅ Profile creation successful")
        
        # Test content creation
        content = UploadedContent.objects.create(
            user=test_user,
            title='DB Test Content',
            subject='Testing',
            file_size=1024,
            processed=True
        )
        print("✅ Content creation successful")
        
        # Test relationships
        session = LearningSession.objects.create(
            student=profile,
            content=content,
            start_time=django.utils.timezone.now()
        )
        print("✅ Relationship creation successful")
        
        # Clean up
        session.delete()
        content.delete()
        profile.delete()
        test_user.delete()
        print("✅ Database cleanup successful")
        
        print("🎉 Database operations completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Database operations failed: {e}")
        return False


def test_cache_operations():
    """Test cache operations"""
    print("\n💾 Testing Cache Operations")
    
    try:
        from django.core.cache import cache
        
        # Test cache set/get
        cache.set('test_key', 'test_value', 30)
        cached_value = cache.get('test_key')
        
        if cached_value == 'test_value':
            print("✅ Cache set/get successful")
        else:
            print("❌ Cache set/get failed")
            return False
        
        # Test cache delete
        cache.delete('test_key')
        deleted_value = cache.get('test_key')
        
        if deleted_value is None:
            print("✅ Cache delete successful")
        else:
            print("❌ Cache delete failed")
            return False
        
        print("🎉 Cache operations completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Cache operations failed: {e}")
        return False


def run_integration_tests():
    """Run all integration tests"""
    print("METLAB.EDU - SYSTEM INTEGRATION TESTS")
    print("=" * 80)
    
    tests = [
        ("System Health", test_system_health),
        ("Database Operations", test_database_operations),
        ("Cache Operations", test_cache_operations),
        ("Student Workflow", test_student_workflow),
        ("Teacher Workflow", test_teacher_workflow),
        ("Parent Workflow", test_parent_workflow),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} Test")
        print("-" * 40)
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name} Test PASSED")
            else:
                print(f"❌ {test_name} Test FAILED")
                
        except Exception as e:
            print(f"❌ {test_name} Test ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 80)
    
    passed_tests = sum(1 for _, result in results if result)
    total_tests = len(results)
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\nDetailed Results:")
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} {test_name}")
    
    all_passed = passed_tests == total_tests
    
    if all_passed:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("✅ System components are properly integrated")
        print("🚀 AI Learning Platform is ready for use")
    else:
        print("\n⚠️ SOME INTEGRATION TESTS FAILED")
        print("❌ Review failed tests before deployment")
    
    print("=" * 80)
    
    return all_passed


if __name__ == '__main__':
    import django.utils.timezone
    success = run_integration_tests()
    exit(0 if success else 1)