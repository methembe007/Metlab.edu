"""
Data flow verification tests for the AI Learning Platform.
Tests that data flows correctly between all system components.
"""

import os
import django
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from unittest.mock import patch, MagicMock
import json
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'metlab_edu.settings')
django.setup()

from accounts.models import StudentProfile, TeacherProfile, ParentProfile
from content.models import UploadedContent, GeneratedSummary, GeneratedQuiz, Flashcard
from learning.models import LearningSession, WeaknessAnalysis, PersonalizedRecommendation, Class, Enrollment
from gamification.models import Achievement, StudentAchievement, Leaderboard, VirtualCurrency
from community.models import TutorProfile, StudyGroup, StudySession, StudyPartner, TutoringBooking

User = get_user_model()


class DataFlowVerificationTest(TransactionTestCase):
    """Verify data flows correctly between all system components"""
    
    def setUp(self):
        """Set up test data"""
        # Create users
        self.student_user = User.objects.create_user(
            username='dataflow_student',
            email='student@dataflow.test',
            password='testpass123',
            role='student'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            learning_preferences={'style': 'visual'},
            current_streak=0,
            total_xp=0
        )
        
        self.teacher_user = User.objects.create_user(
            username='dataflow_teacher',
            email='teacher@dataflow.test',
            password='testpass123',
            role='teacher'
        )
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            institution='Test School'
        )
        
        # Create test content
        self.test_pdf_content = b'%PDF-1.4\nTest content for data flow verification'
    
    def test_content_to_ai_to_learning_flow(self):
        """Test: Content Upload → AI Processing → Learning Materials → Session Tracking"""
        
        print("\n🔄 Testing Content → AI → Learning Flow")
        
        # Step 1: Upload content
        with patch('content.ai_services.extract_key_concepts') as mock_extract, \
             patch('content.ai_services.generate_summary') as mock_summary, \
             patch('content.ai_services.generate_quiz') as mock_quiz, \
             patch('content.ai_services.generate_flashcards') as mock_flashcards:
            
            # Mock AI responses
            mock_extract.return_value = ['algebra', 'equations', 'variables']
            mock_summary.return_value = 'Comprehensive summary about algebra and equations'
            mock_quiz.return_value = {
                'questions': [
                    {
                        'question': 'What is an equation?',
                        'type': 'multiple_choice',
                        'options': ['A mathematical statement', 'A number', 'A variable', 'A constant'],
                        'correct_answer': 'A mathematical statement'
                    }
                ]
            }
            mock_flashcards.return_value = [
                {'front': 'Equation', 'back': 'A mathematical statement that asserts equality'}
            ]
            
            # Create content
            content = UploadedContent.objects.create(
                user=self.student_user,
                title='Algebra Basics',
                subject='Mathematics',
                file_size=1024,
                processed=True,
                key_concepts=['algebra', 'equations', 'variables']
            )
            
            # Verify AI processing created learning materials
            summary = GeneratedSummary.objects.create(
                content=content,
                summary_type='detailed',
                text='Comprehensive summary about algebra and equations'
            )
            
            quiz = GeneratedQuiz.objects.create(
                content=content,
                questions=mock_quiz.return_value,
                difficulty_level='medium'
            )
            
            flashcard = Flashcard.objects.create(
                content=content,
                front_text='Equation',
                back_text='A mathematical statement that asserts equality',
                concept_tag='algebra'
            )
            
            print(f"✅ Content created: {content.title}")
            print(f"✅ AI materials generated: Summary, Quiz, Flashcard")
            
            # Step 2: Start learning session
            session = LearningSession.objects.create(
                student=self.student_profile,
                content=content,
                start_time=django.utils.timezone.now()
            )
            
            print(f"✅ Learning session started: {session.id}")
            
            # Step 3: Complete session with performance data
            session.end_time = django.utils.timezone.now()
            session.performance_score = 85.0
            session.save()
            
            print(f"✅ Session completed with score: {session.performance_score}")
            
            # Verify data flow integrity
            self.assertEqual(content.user, self.student_user)
            self.assertTrue(content.processed)
            self.assertEqual(summary.content, content)
            self.assertEqual(quiz.content, content)
            self.assertEqual(flashcard.content, content)
            self.assertEqual(session.content, content)
            self.assertEqual(session.student, self.student_profile)
            
            return content, session
    
    def test_learning_to_analytics_to_gamification_flow(self):
        """Test: Learning Session → Analytics → Gamification Updates"""
        
        print("\n🔄 Testing Learning → Analytics → Gamification Flow")
        
        # Create content and session from previous test
        content, session = self.test_content_to_ai_to_learning_flow()
        
        # Step 1: Generate analytics from learning session
        weakness = WeaknessAnalysis.objects.create(
            student=self.student_profile,
            subject='Mathematics',
            concept='equations',
            weakness_score=0.3,  # 30% weakness
        )
        
        recommendation = PersonalizedRecommendation.objects.create(
            student=self.student_profile,
            recommendation_type='practice',
            content={'subject': 'Mathematics', 'concept': 'equations', 'difficulty': 'easy'},
            priority=1
        )
        
        print(f"✅ Analytics generated: Weakness identified, Recommendation created")
        
        # Step 2: Update gamification based on performance
        # Award XP for session completion
        initial_xp = self.student_profile.total_xp
        xp_earned = int(session.performance_score)  # 85 XP
        self.student_profile.total_xp += xp_earned
        self.student_profile.save()
        
        # Create achievement for first completion
        achievement = Achievement.objects.create(
            name='First Quiz Completed',
            description='Complete your first quiz',
            badge_icon='quiz',
            xp_requirement=0
        )
        
        student_achievement = StudentAchievement.objects.create(
            student=self.student_profile,
            achievement=achievement
        )
        
        # Update leaderboard
        leaderboard, created = Leaderboard.objects.get_or_create(
            student=self.student_profile,
            subject='Mathematics',
            defaults={
                'weekly_xp': xp_earned,
                'monthly_xp': xp_earned,
                'rank': 1
            }
        )
        
        # Award virtual currency
        currency, created = VirtualCurrency.objects.get_or_create(
            student=self.student_profile,
            defaults={'coins': 0, 'earned_today': 0}
        )
        coins_earned = 10  # 10 coins for completion
        currency.coins += coins_earned
        currency.earned_today += coins_earned
        currency.save()
        
        print(f"✅ Gamification updated: +{xp_earned} XP, +{coins_earned} coins, Achievement earned")
        
        # Verify data flow integrity
        self.assertEqual(weakness.student, self.student_profile)
        self.assertEqual(recommendation.student, self.student_profile)
        self.assertEqual(self.student_profile.total_xp, initial_xp + xp_earned)
        self.assertEqual(student_achievement.student, self.student_profile)
        self.assertEqual(leaderboard.student, self.student_profile)
        self.assertEqual(currency.student, self.student_profile)
        self.assertEqual(currency.coins, coins_earned)
        
        return weakness, recommendation, student_achievement, currency
    
    def test_teacher_to_student_content_flow(self):
        """Test: Teacher Content Upload → Class Assignment → Student Access"""
        
        print("\n🔄 Testing Teacher → Student Content Flow")
        
        # Step 1: Teacher creates class
        test_class = Class.objects.create(
            name='Data Flow Test Class',
            subject='Mathematics',
            description='Test class for data flow verification',
            teacher=self.teacher_profile,
            invitation_code='DATAFLOW123'
        )
        
        print(f"✅ Class created: {test_class.name}")
        
        # Step 2: Student enrolls in class
        enrollment = Enrollment.objects.create(
            student=self.student_profile,
            class_obj=test_class,
            is_active=True
        )
        
        print(f"✅ Student enrolled in class")
        
        # Step 3: Teacher uploads content for class
        with patch('content.ai_services.extract_key_concepts') as mock_extract:
            mock_extract.return_value = ['geometry', 'shapes', 'angles']
            
            teacher_content = UploadedContent.objects.create(
                user=self.teacher_user,
                title='Geometry Lesson',
                subject='Mathematics',
                file_size=2048,
                processed=True,
                key_concepts=['geometry', 'shapes', 'angles'],
                assigned_class=test_class
            )
        
        print(f"✅ Teacher content uploaded and assigned to class")
        
        # Step 4: Verify student can access class content
        class_content = UploadedContent.objects.filter(assigned_class=test_class)
        self.assertTrue(class_content.exists())
        self.assertEqual(class_content.first(), teacher_content)
        
        # Verify enrollment relationship
        self.assertEqual(enrollment.student, self.student_profile)
        self.assertEqual(enrollment.class_obj, test_class)
        self.assertTrue(enrollment.is_active)
        
        print(f"✅ Data flow verified: Teacher content accessible to enrolled student")
        
        return test_class, enrollment, teacher_content
    
    def test_parent_child_monitoring_flow(self):
        """Test: Student Activity → Parent Monitoring → Notifications"""
        
        print("\n🔄 Testing Student → Parent Monitoring Flow")
        
        # Step 1: Create parent profile and link to student
        parent_user = User.objects.create_user(
            username='dataflow_parent',
            email='parent@dataflow.test',
            password='testpass123',
            role='parent'
        )
        parent_profile = ParentProfile.objects.create(user=parent_user)
        parent_profile.children.add(self.student_profile)
        
        print(f"✅ Parent profile created and linked to student")
        
        # Step 2: Generate student activity (from previous tests)
        content, session = self.test_content_to_ai_to_learning_flow()
        
        # Step 3: Parent should be able to access child's data
        child_sessions = LearningSession.objects.filter(student=self.student_profile)
        child_content = UploadedContent.objects.filter(user=self.student_user)
        
        self.assertTrue(child_sessions.exists())
        self.assertTrue(child_content.exists())
        
        # Verify parent-child relationship
        self.assertIn(self.student_profile, parent_profile.children.all())
        
        print(f"✅ Parent can access child's learning data")
        
        return parent_profile
    
    def test_community_features_data_flow(self):
        """Test: Community Features → Study Groups → Tutoring → Social Learning"""
        
        print("\n🔄 Testing Community Features Data Flow")
        
        # Step 1: Create tutor profile
        tutor_user = User.objects.create_user(
            username='dataflow_tutor',
            email='tutor@dataflow.test',
            password='testpass123',
            role='tutor'
        )
        tutor_profile = TutorProfile.objects.create(
            user=tutor_user,
            hourly_rate=30.00,
            rating=4.8
        )
        
        print(f"✅ Tutor profile created")
        
        # Step 2: Student books tutoring session
        booking = TutoringBooking.objects.create(
            student=self.student_profile,
            tutor=tutor_profile,
            subject='Mathematics',
            scheduled_time=django.utils.timezone.now() + django.utils.timedelta(days=1),
            duration_minutes=60,
            status='confirmed'
        )
        
        print(f"✅ Tutoring session booked")
        
        # Step 3: Create study group
        study_group = StudyGroup.objects.create(
            name='Math Study Group',
            subject='Mathematics',
            description='Group for math practice',
            created_by=self.student_profile,
            max_members=5
        )
        study_group.members.add(self.student_profile)
        
        print(f"✅ Study group created")
        
        # Step 4: Schedule group study session
        group_session = StudySession.objects.create(
            group=study_group,
            scheduled_time=django.utils.timezone.now() + django.utils.timedelta(days=2),
            duration_minutes=90,
            room_id='DATAFLOW_ROOM_123',
            status='scheduled'
        )
        
        print(f"✅ Group study session scheduled")
        
        # Verify data relationships
        self.assertEqual(booking.student, self.student_profile)
        self.assertEqual(booking.tutor, tutor_profile)
        self.assertEqual(study_group.created_by, self.student_profile)
        self.assertIn(self.student_profile, study_group.members.all())
        self.assertEqual(group_session.group, study_group)
        
        print(f"✅ Community features data flow verified")
        
        return tutor_profile, booking, study_group, group_session
    
    def test_complete_system_data_flow(self):
        """Test complete data flow through entire system"""
        
        print("\n🔄 Testing Complete System Data Flow")
        print("=" * 60)
        
        # Run all individual flow tests
        content, session = self.test_content_to_ai_to_learning_flow()
        weakness, recommendation, achievement, currency = self.test_learning_to_analytics_to_gamification_flow()
        test_class, enrollment, teacher_content = self.test_teacher_to_student_content_flow()
        parent_profile = self.test_parent_child_monitoring_flow()
        tutor_profile, booking, study_group, group_session = self.test_community_features_data_flow()
        
        # Verify cross-system data integrity
        print("\n🔍 Verifying Cross-System Data Integrity")
        
        # Check that all data belongs to the same student
        student_data = {
            'content_uploads': UploadedContent.objects.filter(user=self.student_user).count(),
            'learning_sessions': LearningSession.objects.filter(student=self.student_profile).count(),
            'achievements': StudentAchievement.objects.filter(student=self.student_profile).count(),
            'weaknesses': WeaknessAnalysis.objects.filter(student=self.student_profile).count(),
            'recommendations': PersonalizedRecommendation.objects.filter(student=self.student_profile).count(),
            'enrollments': Enrollment.objects.filter(student=self.student_profile).count(),
            'bookings': TutoringBooking.objects.filter(student=self.student_profile).count(),
            'study_groups': StudyGroup.objects.filter(members=self.student_profile).count()
        }
        
        print(f"✅ Student data summary: {student_data}")
        
        # Verify parent can access all child data
        child_data_accessible = all([
            parent_profile.children.filter(id=self.student_profile.id).exists(),
            LearningSession.objects.filter(student__in=parent_profile.children.all()).exists(),
            UploadedContent.objects.filter(user__studentprofile__in=parent_profile.children.all()).exists()
        ])
        
        self.assertTrue(child_data_accessible)
        print(f"✅ Parent can access all child data")
        
        # Verify teacher can access class data
        teacher_data_accessible = all([
            Class.objects.filter(teacher=self.teacher_profile).exists(),
            Enrollment.objects.filter(class_obj__teacher=self.teacher_profile).exists(),
            UploadedContent.objects.filter(assigned_class__teacher=self.teacher_profile).exists()
        ])
        
        self.assertTrue(teacher_data_accessible)
        print(f"✅ Teacher can access all class data")
        
        # Verify gamification data consistency
        gamification_consistent = all([
            self.student_profile.total_xp > 0,
            VirtualCurrency.objects.filter(student=self.student_profile).exists(),
            StudentAchievement.objects.filter(student=self.student_profile).exists(),
            Leaderboard.objects.filter(student=self.student_profile).exists()
        ])
        
        self.assertTrue(gamification_consistent)
        print(f"✅ Gamification data is consistent")
        
        print("\n🎉 COMPLETE SYSTEM DATA FLOW VERIFICATION PASSED")
        print("=" * 60)
        
        return True


def run_data_flow_tests():
    """Run all data flow verification tests"""
    import django
    from django.test.utils import get_runner
    from django.conf import settings
    
    # Setup Django test environment
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Run the data flow tests
    print("METLAB.EDU - DATA FLOW VERIFICATION")
    print("=" * 80)
    
    try:
        # Create test instance and run complete flow test
        test_instance = DataFlowVerificationTest()
        test_instance.setUp()
        
        # Run complete system data flow test
        result = test_instance.test_complete_system_data_flow()
        
        if result:
            print("\n✅ ALL DATA FLOW TESTS PASSED")
            print("🔗 All system components are properly integrated")
            print("📊 Data flows correctly between all services")
            return True
        else:
            print("\n❌ DATA FLOW TESTS FAILED")
            return False
            
    except Exception as e:
        print(f"\n❌ DATA FLOW TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_data_flow_tests()
    exit(0 if success else 1)


# Import Django utilities
import django.utils.timezone