"""
Simple integration validation for AI Learning Platform
Validates core system components and data flow
"""

import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'metlab_edu.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import connection
from django.core.cache import cache
from accounts.models import StudentProfile, TeacherProfile, ParentProfile
from content.models import UploadedContent
from learning.models import LearningSession, WeaknessAnalysis, PersonalizedRecommendation
from gamification.models import Achievement, VirtualCurrency
from community.models import StudyGroup

User = get_user_model()


def validate_database_connection():
    """Test database connectivity"""
    print("🗄️ Validating Database Connection...")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        if result[0] == 1:
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


def validate_cache_system():
    """Test cache functionality"""
    print("💾 Validating Cache System...")
    try:
        # Test cache operations
        cache.set('validation_key', 'validation_value', 30)
        value = cache.get('validation_key')
        if value == 'validation_value':
            print("✅ Cache operations successful")
            cache.delete('validation_key')
            return True
        else:
            print("❌ Cache operations failed")
            return False
    except Exception as e:
        print(f"❌ Cache error: {e}")
        return False


def validate_user_models():
    """Test user model creation and relationships"""
    print("👤 Validating User Models...")
    try:
        # Create test student
        student_user = User.objects.create_user(
            username='validation_student',
            email='student@validation.test',
            password='testpass123',
            role='student'
        )
        
        student_profile = StudentProfile.objects.create(
            user=student_user,
            learning_preferences={'style': 'visual'},
            current_streak=0,
            total_xp=0
        )
        
        # Create test teacher
        teacher_user = User.objects.create_user(
            username='validation_teacher',
            email='teacher@validation.test',
            password='testpass123',
            role='teacher'
        )
        
        teacher_profile = TeacherProfile.objects.create(
            user=teacher_user,
            institution='Validation School'
        )
        
        # Create test parent
        parent_user = User.objects.create_user(
            username='validation_parent',
            email='parent@validation.test',
            password='testpass123',
            role='parent'
        )
        
        parent_profile = ParentProfile.objects.create(user=parent_user)
        parent_profile.children.add(student_profile)
        
        print("✅ User models created successfully")
        
        # Test relationships
        if parent_profile.children.filter(id=student_profile.id).exists():
            print("✅ Parent-child relationship working")
        else:
            print("❌ Parent-child relationship failed")
            return False
        
        # Clean up
        parent_profile.delete()
        teacher_profile.delete()
        student_profile.delete()
        parent_user.delete()
        teacher_user.delete()
        student_user.delete()
        
        print("✅ User model validation completed")
        return True
        
    except Exception as e:
        print(f"❌ User model error: {e}")
        return False


def validate_content_models():
    """Test content model creation"""
    print("📄 Validating Content Models...")
    try:
        # Clean up any existing test users first
        User.objects.filter(username='content_test_user').delete()
        
        # Create test user
        user = User.objects.create_user(
            username='content_test_user',
            email='content@test.com',
            password='testpass123',
            role='student'
        )
        
        # Create content
        content = UploadedContent.objects.create(
            user=user,
            original_filename='test.pdf',
            file_size=1024,
            content_type='pdf',
            processing_status='completed'
        )
        
        print("✅ Content model created successfully")
        
        # Clean up
        content.delete()
        user.delete()
        
        return True
        
    except Exception as e:
        print(f"❌ Content model error: {e}")
        return False


def validate_learning_models():
    """Test learning model creation and relationships"""
    print("📚 Validating Learning Models...")
    try:
        # Clean up any existing test users first
        User.objects.filter(username='learning_test_user').delete()
        
        # Create test user and profile
        user = User.objects.create_user(
            username='learning_test_user',
            email='learning@test.com',
            password='testpass123',
            role='student'
        )
        
        profile = StudentProfile.objects.create(
            user=user,
            learning_preferences={'style': 'visual'},
            current_streak=0,
            total_xp=0
        )
        
        # Create content
        content = UploadedContent.objects.create(
            user=user,
            original_filename='test.pdf',
            file_size=1024,
            content_type='pdf',
            processing_status='completed'
        )
        
        # Create learning session
        session = LearningSession.objects.create(
            student=profile,
            content=content,
            session_type='quiz',
            start_time=django.utils.timezone.now()
        )
        
        # Create weakness analysis
        weakness = WeaknessAnalysis.objects.create(
            student=profile,
            subject='Mathematics',
            concept='Algebra',
            weakness_score=75.0,
            weakness_level='high'
        )
        
        # Create recommendation
        recommendation = PersonalizedRecommendation.objects.create(
            student=profile,
            recommendation_type='practice',
            title='Practice Algebra',
            description='Focus on algebra concepts',
            content={'subject': 'Mathematics'},
            priority=3
        )
        
        print("✅ Learning models created successfully")
        
        # Test relationships
        if session.student == profile and session.content == content:
            print("✅ Learning session relationships working")
        else:
            print("❌ Learning session relationships failed")
            return False
        
        # Clean up
        recommendation.delete()
        weakness.delete()
        session.delete()
        content.delete()
        profile.delete()
        user.delete()
        
        return True
        
    except Exception as e:
        print(f"❌ Learning model error: {e}")
        return False


def validate_gamification_models():
    """Test gamification model creation"""
    print("🎮 Validating Gamification Models...")
    try:
        # Clean up any existing test users first
        User.objects.filter(username='gamification_test_user').delete()
        
        # Create test user and profile
        user = User.objects.create_user(
            username='gamification_test_user',
            email='gamification@test.com',
            password='testpass123',
            role='student'
        )
        
        profile = StudentProfile.objects.create(
            user=user,
            learning_preferences={'style': 'visual'},
            current_streak=0,
            total_xp=0
        )
        
        # Create achievement
        achievement = Achievement.objects.create(
            name='Test Achievement',
            description='Achievement for testing',
            badge_icon='test',
            xp_requirement=0
        )
        
        # Create virtual currency
        currency = VirtualCurrency.objects.create(
            student=profile,
            coins=100,
            earned_today=10
        )
        
        print("✅ Gamification models created successfully")
        
        # Clean up
        currency.delete()
        achievement.delete()
        profile.delete()
        user.delete()
        
        return True
        
    except Exception as e:
        print(f"❌ Gamification model error: {e}")
        return False


def validate_community_models():
    """Test community model creation"""
    print("👥 Validating Community Models...")
    try:
        # Clean up any existing test users first
        User.objects.filter(username='community_test_user').delete()
        
        # Create test user and profile
        user = User.objects.create_user(
            username='community_test_user',
            email='community@test.com',
            password='testpass123',
            role='student'
        )
        
        profile = StudentProfile.objects.create(
            user=user,
            learning_preferences={'style': 'visual'},
            current_streak=0,
            total_xp=0
        )
        
        # Create subject first
        from community.models import Subject
        subject = Subject.objects.create(
            name='Mathematics',
            description='Mathematics subject'
        )
        
        # Create study group
        study_group = StudyGroup.objects.create(
            name='Test Study Group',
            subject=subject,
            description='Group for testing',
            created_by=profile,
            max_members=5
        )
        study_group.members.add(profile)
        
        print("✅ Community models created successfully")
        
        # Test relationships
        if study_group.created_by == profile and profile in study_group.members.all():
            print("✅ Study group relationships working")
        else:
            print("❌ Study group relationships failed")
            return False
        
        # Clean up
        study_group.delete()
        subject.delete()
        profile.delete()
        user.delete()
        
        return True
        
    except Exception as e:
        print(f"❌ Community model error: {e}")
        return False


def validate_data_flow():
    """Test complete data flow between components"""
    print("🔄 Validating Complete Data Flow...")
    try:
        # Clean up any existing test users first
        User.objects.filter(username='dataflow_student').delete()
        
        # Create student
        student_user = User.objects.create_user(
            username='dataflow_student',
            email='dataflow@test.com',
            password='testpass123',
            role='student'
        )
        
        student_profile = StudentProfile.objects.create(
            user=student_user,
            learning_preferences={'style': 'visual'},
            current_streak=0,
            total_xp=0
        )
        
        # Create content
        content = UploadedContent.objects.create(
            user=student_user,
            original_filename='dataflow_test.pdf',
            file_size=1024,
            content_type='pdf',
            processing_status='completed'
        )
        
        # Create learning session
        session = LearningSession.objects.create(
            student=student_profile,
            content=content,
            session_type='quiz',
            start_time=django.utils.timezone.now(),
            performance_score=85.0,
            questions_attempted=10,
            questions_correct=8
        )
        
        # Create weakness analysis based on session
        weakness = WeaknessAnalysis.objects.create(
            student=student_profile,
            subject='Mathematics',
            concept='Algebra',
            weakness_score=30.0,
            weakness_level='medium',
            total_attempts=session.questions_attempted,
            correct_attempts=session.questions_correct
        )
        
        # Create recommendation based on weakness
        recommendation = PersonalizedRecommendation.objects.create(
            student=student_profile,
            recommendation_type='practice',
            title='Practice Algebra',
            description='Focus on algebra concepts',
            content={'subject': 'Mathematics'},
            priority=3,
            related_weakness=weakness,
            related_content=content
        )
        
        # Update gamification
        student_profile.total_xp += 50
        student_profile.save()
        
        currency = VirtualCurrency.objects.create(
            student=student_profile,
            coins=20,
            earned_today=20
        )
        
        print("✅ Complete data flow created successfully")
        
        # Verify data relationships
        checks = [
            (session.student == student_profile, "Session-Student relationship"),
            (session.content == content, "Session-Content relationship"),
            (weakness.student == student_profile, "Weakness-Student relationship"),
            (recommendation.student == student_profile, "Recommendation-Student relationship"),
            (recommendation.related_weakness == weakness, "Recommendation-Weakness relationship"),
            (recommendation.related_content == content, "Recommendation-Content relationship"),
            (currency.student == student_profile, "Currency-Student relationship"),
            (student_profile.total_xp == 50, "XP update"),
        ]
        
        all_passed = True
        for check, description in checks:
            if check:
                print(f"✅ {description}")
            else:
                print(f"❌ {description}")
                all_passed = False
        
        # Clean up
        currency.delete()
        recommendation.delete()
        weakness.delete()
        session.delete()
        content.delete()
        student_profile.delete()
        student_user.delete()
        
        if all_passed:
            print("✅ Complete data flow validation passed")
            return True
        else:
            print("❌ Some data flow checks failed")
            return False
        
    except Exception as e:
        print(f"❌ Data flow error: {e}")
        return False


def run_validation():
    """Run complete system validation"""
    print("METLAB.EDU - SYSTEM INTEGRATION VALIDATION")
    print("=" * 80)
    
    validations = [
        ("Database Connection", validate_database_connection),
        ("Cache System", validate_cache_system),
        ("User Models", validate_user_models),
        ("Content Models", validate_content_models),
        ("Learning Models", validate_learning_models),
        ("Gamification Models", validate_gamification_models),
        ("Community Models", validate_community_models),
        ("Complete Data Flow", validate_data_flow),
    ]
    
    results = []
    
    for name, validation_func in validations:
        print(f"\n{'='*20} {name} {'='*20}")
        try:
            result = validation_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} validation failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"Total Validations: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    print("\nDetailed Results:")
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} {name}")
    
    all_passed = passed == total
    
    if all_passed:
        print("\n🎉 ALL VALIDATIONS PASSED!")
        print("✅ System components are properly integrated")
        print("🔗 Data flows correctly between all services")
        print("🚀 AI Learning Platform integration is successful")
    else:
        print("\n⚠️ SOME VALIDATIONS FAILED")
        print("❌ Review failed validations")
        print("🔧 System needs attention before full deployment")
    
    print("=" * 80)
    
    return all_passed


if __name__ == '__main__':
    import django.utils.timezone
    success = run_validation()
    exit(0 if success else 1)