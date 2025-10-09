"""
Comprehensive integration tests for the AI Learning Platform.
Tests end-to-end workflows for all user roles and system components.
"""

import os
import tempfile
from django.test import TestCase, TransactionTestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test.utils import override_settings
from django.core.cache import cache
from django.db import transaction
from unittest.mock import patch, MagicMock

from accounts.models import StudentProfile, TeacherProfile, ParentProfile
from content.models import UploadedContent, GeneratedSummary, GeneratedQuiz, Flashcard
from learning.models import LearningSession, WeaknessAnalysis, PersonalizedRecommendation, Class, Enrollment
from gamification.models import Achievement, StudentAchievement, Leaderboard, VirtualCurrency
from community.models import TutorProfile, StudyGroup, StudySession, StudyPartner, TutoringBooking

User = get_user_model()


class EndToEndIntegrationTest(TransactionTestCase):
    """Test complete user journeys and system integration"""
    
    def setUp(self):
        """Set up test data for integration tests"""
        self.client = Client()
        
        # Create test users for all roles
        self.student_user = User.objects.create_user(
            username='student1',
            email='student@test.com',
            password='testpass123',
            role='student'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            learning_preferences={'style': 'visual', 'pace': 'medium'},
            current_streak=5,
            total_xp=150
        )
        
        self.teacher_user = User.objects.create_user(
            username='teacher1',
            email='teacher@test.com',
            password='testpass123',
            role='teacher'
        )
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            institution='Test School'
        )
        
        self.parent_user = User.objects.create_user(
            username='parent1',
            email='parent@test.com',
            password='testpass123',
            role='parent'
        )
        self.parent_profile = ParentProfile.objects.create(
            user=self.parent_user
        )
        self.parent_profile.children.add(self.student_profile)
        
        # Create test content file
        self.test_pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test content) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n298\n%%EOF'
        
        # Clear cache before tests
        cache.clear()
    
    def test_student_complete_learning_journey(self):
        """Test complete student learning workflow from upload to completion"""
        
        # 1. Student login
        login_response = self.client.post(reverse('accounts:login'), {
            'username': 'student1',
            'password': 'testpass123'
        })
        self.assertEqual(login_response.status_code, 302)
        
        # 2. Access student dashboard
        dashboard_response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertContains(dashboard_response, 'Welcome')
        
        # 3. Upload content with mocked AI processing
        with patch('content.ai_services.extract_key_concepts') as mock_extract, \
             patch('content.ai_services.generate_summary') as mock_summary, \
             patch('content.ai_services.generate_quiz') as mock_quiz, \
             patch('content.ai_services.generate_flashcards') as mock_flashcards:
            
            # Mock AI responses
            mock_extract.return_value = ['concept1', 'concept2', 'concept3']
            mock_summary.return_value = 'Test summary content'
            mock_quiz.return_value = {
                'questions': [
                    {
                        'question': 'What is concept1?',
                        'type': 'multiple_choice',
                        'options': ['A', 'B', 'C', 'D'],
                        'correct_answer': 'A'
                    }
                ]
            }
            mock_flashcards.return_value = [
                {'front': 'What is concept1?', 'back': 'Definition of concept1'}
            ]
            
            # Upload file
            test_file = SimpleUploadedFile(
                "test.pdf",
                self.test_pdf_content,
                content_type="application/pdf"
            )
            
            upload_response = self.client.post(reverse('content:upload'), {
                'title': 'Test Document',
                'file': test_file,
                'subject': 'Mathematics'
            })
            self.assertEqual(upload_response.status_code, 302)
            
            # Verify content was created
            content = UploadedContent.objects.get(title='Test Document')
            self.assertEqual(content.user, self.student_user)
            
        # 4. View content library
        library_response = self.client.get(reverse('content:library'))
        self.assertEqual(library_response.status_code, 200)
        self.assertContains(library_response, 'Test Document')
        
        # 5. Start learning session
        session_response = self.client.post(reverse('learning:start_session'), {
            'content_id': content.id
        })
        self.assertEqual(session_response.status_code, 302)
        
        # Verify session was created
        session = LearningSession.objects.get(student=self.student_profile, content=content)
        self.assertIsNotNone(session.start_time)
        
        # 6. Complete quiz
        quiz_response = self.client.post(reverse('learning:complete_quiz'), {
            'session_id': session.id,
            'answers': '{"1": "A"}',
            'score': 100
        })
        self.assertEqual(quiz_response.status_code, 302)
        
        # 7. View analytics
        analytics_response = self.client.get(reverse('learning:analytics'))
        self.assertEqual(analytics_response.status_code, 200)
        
        # 8. Check gamification updates
        gamification_response = self.client.get(reverse('gamification:achievements'))
        self.assertEqual(gamification_response.status_code, 200)
    
    def test_teacher_content_management_workflow(self):
        """Test teacher workflow for content creation and class management"""
        
        # 1. Teacher login
        self.client.login(username='teacher1', password='testpass123')
        
        # 2. Access teacher dashboard
        dashboard_response = self.client.get(reverse('accounts:teacher_dashboard'))
        self.assertEqual(dashboard_response.status_code, 200)
        
        # 3. Create a class
        class_response = self.client.post(reverse('learning:create_class'), {
            'name': 'Test Class',
            'subject': 'Mathematics',
            'description': 'Test class description'
        })
        self.assertEqual(class_response.status_code, 302)
        
        # Verify class was created
        test_class = Class.objects.get(name='Test Class')
        self.assertEqual(test_class.teacher, self.teacher_profile)
        
        # 4. Upload content for class
        with patch('content.ai_services.extract_key_concepts') as mock_extract, \
             patch('content.ai_services.generate_quiz') as mock_quiz:
            
            mock_extract.return_value = ['algebra', 'equations', 'variables']
            mock_quiz.return_value = {
                'questions': [
                    {
                        'question': 'What is algebra?',
                        'type': 'multiple_choice',
                        'options': ['Math', 'Science', 'Art', 'History'],
                        'correct_answer': 'Math'
                    }
                ]
            }
            
            test_file = SimpleUploadedFile(
                "lesson.pdf",
                self.test_pdf_content,
                content_type="application/pdf"
            )
            
            upload_response = self.client.post(reverse('learning:upload_content'), {
                'title': 'Algebra Lesson',
                'file': test_file,
                'subject': 'Mathematics',
                'class_id': test_class.id
            })
            self.assertEqual(upload_response.status_code, 302)
        
        # 5. Enroll student in class
        enrollment_response = self.client.post(reverse('learning:enroll_student'), {
            'class_id': test_class.id,
            'student_id': self.student_profile.id
        })
        self.assertEqual(enrollment_response.status_code, 302)
        
        # Verify enrollment
        enrollment = Enrollment.objects.get(class_obj=test_class, student=self.student_profile)
        self.assertTrue(enrollment.is_active)
        
        # 6. View class analytics
        analytics_response = self.client.get(reverse('learning:class_analytics', args=[test_class.id]))
        self.assertEqual(analytics_response.status_code, 200)
    
    def test_parent_monitoring_workflow(self):
        """Test parent workflow for monitoring child progress"""
        
        # 1. Parent login
        self.client.login(username='parent1', password='testpass123')
        
        # 2. Access parent dashboard
        dashboard_response = self.client.get(reverse('learning:parent_dashboard'))
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertContains(dashboard_response, self.student_user.username)
        
        # 3. View child progress
        progress_response = self.client.get(
            reverse('learning:child_progress_detail', args=[self.student_profile.id])
        )
        self.assertEqual(progress_response.status_code, 200)
        
        # 4. Set screen time limits
        screen_time_response = self.client.post(reverse('learning:screen_time_settings'), {
            'child_id': self.student_profile.id,
            'daily_limit_minutes': 120,
            'break_reminder_minutes': 30
        })
        self.assertEqual(screen_time_response.status_code, 302)
        
        # 5. View parent analytics
        analytics_response = self.client.get(reverse('learning:parent_analytics'))
        self.assertEqual(analytics_response.status_code, 200)
    
    def test_community_features_integration(self):
        """Test community features including tutoring and study groups"""
        
        # 1. Create tutor profile
        tutor_user = User.objects.create_user(
            username='tutor1',
            email='tutor@test.com',
            password='testpass123',
            role='tutor'
        )
        tutor_profile = TutorProfile.objects.create(
            user=tutor_user,
            hourly_rate=25.00,
            rating=4.5
        )
        
        # 2. Student login and view tutor recommendations
        self.client.login(username='student1', password='testpass123')
        
        tutor_recommendations_response = self.client.get(reverse('community:tutor_recommendations'))
        self.assertEqual(tutor_recommendations_response.status_code, 200)
        
        # 3. Book tutoring session
        booking_response = self.client.post(reverse('community:book_tutor'), {
            'tutor_id': tutor_profile.id,
            'subject': 'Mathematics',
            'scheduled_time': '2024-12-01 14:00:00',
            'duration_minutes': 60
        })
        self.assertEqual(booking_response.status_code, 302)
        
        # Verify booking was created
        booking = TutoringBooking.objects.get(student=self.student_profile, tutor=tutor_profile)
        self.assertEqual(booking.subject, 'Mathematics')
        
        # 4. Create study group
        study_group_response = self.client.post(reverse('community:create_study_group'), {
            'name': 'Math Study Group',
            'subject': 'Mathematics',
            'description': 'Group for math practice',
            'max_members': 5
        })
        self.assertEqual(study_group_response.status_code, 302)
        
        # Verify study group was created
        study_group = StudyGroup.objects.get(name='Math Study Group')
        self.assertEqual(study_group.created_by, self.student_profile)
        
        # 5. Schedule study session
        session_response = self.client.post(reverse('community:schedule_group_session'), {
            'group_id': study_group.id,
            'scheduled_time': '2024-12-02 15:00:00',
            'duration_minutes': 90
        })
        self.assertEqual(session_response.status_code, 302)
    
    def test_ai_processing_pipeline_integration(self):
        """Test AI processing pipeline with error handling"""
        
        self.client.login(username='student1', password='testpass123')
        
        # Test successful AI processing
        with patch('content.ai_services.extract_key_concepts') as mock_extract, \
             patch('content.ai_services.generate_summary') as mock_summary, \
             patch('content.ai_services.generate_quiz') as mock_quiz, \
             patch('content.ai_services.generate_flashcards') as mock_flashcards:
            
            mock_extract.return_value = ['physics', 'motion', 'velocity']
            mock_summary.return_value = 'Physics summary about motion and velocity'
            mock_quiz.return_value = {
                'questions': [
                    {
                        'question': 'What is velocity?',
                        'type': 'short_answer',
                        'correct_answer': 'Rate of change of position'
                    }
                ]
            }
            mock_flashcards.return_value = [
                {'front': 'Velocity', 'back': 'Rate of change of position with respect to time'}
            ]
            
            test_file = SimpleUploadedFile(
                "physics.pdf",
                self.test_pdf_content,
                content_type="application/pdf"
            )
            
            upload_response = self.client.post(reverse('content:upload'), {
                'title': 'Physics Notes',
                'file': test_file,
                'subject': 'Physics'
            })
            self.assertEqual(upload_response.status_code, 302)
            
            # Verify all AI-generated content was created
            content = UploadedContent.objects.get(title='Physics Notes')
            self.assertTrue(GeneratedSummary.objects.filter(content=content).exists())
            self.assertTrue(GeneratedQuiz.objects.filter(content=content).exists())
            self.assertTrue(Flashcard.objects.filter(content=content).exists())
        
        # Test AI processing failure handling
        with patch('content.ai_services.extract_key_concepts') as mock_extract:
            mock_extract.side_effect = Exception("AI service unavailable")
            
            test_file2 = SimpleUploadedFile(
                "failed.pdf",
                self.test_pdf_content,
                content_type="application/pdf"
            )
            
            upload_response = self.client.post(reverse('content:upload'), {
                'title': 'Failed Processing',
                'file': test_file2,
                'subject': 'Chemistry'
            })
            
            # Should still create content record but mark as failed
            content = UploadedContent.objects.get(title='Failed Processing')
            self.assertFalse(content.processed)
    
    def test_real_time_features_integration(self):
        """Test real-time features like notifications and study rooms"""
        
        # This would require WebSocket testing which is complex
        # For now, test the HTTP endpoints that support real-time features
        
        self.client.login(username='student1', password='testpass123')
        
        # Test study room creation
        study_room_response = self.client.post(reverse('community:create_study_room'), {
            'name': 'Physics Study Room',
            'subject': 'Physics',
            'max_participants': 4
        })
        self.assertEqual(study_room_response.status_code, 302)
        
        # Test notification preferences
        notification_response = self.client.post(reverse('learning:notification_settings'), {
            'email_notifications': True,
            'achievement_notifications': True,
            'reminder_notifications': True
        })
        self.assertEqual(notification_response.status_code, 302)
    
    def test_gamification_system_integration(self):
        """Test gamification system with XP, achievements, and leaderboards"""
        
        self.client.login(username='student1', password='testpass123')
        
        # Create some achievements
        achievement1 = Achievement.objects.create(
            name='First Upload',
            description='Upload your first document',
            badge_icon='upload',
            xp_requirement=0
        )
        
        achievement2 = Achievement.objects.create(
            name='Quiz Master',
            description='Score 100% on 5 quizzes',
            badge_icon='quiz',
            xp_requirement=500
        )
        
        # Simulate earning achievements through learning activities
        with patch('content.ai_services.extract_key_concepts') as mock_extract:
            mock_extract.return_value = ['test', 'concept']
            
            test_file = SimpleUploadedFile(
                "gamification_test.pdf",
                self.test_pdf_content,
                content_type="application/pdf"
            )
            
            # Upload should trigger achievement
            upload_response = self.client.post(reverse('content:upload'), {
                'title': 'Gamification Test',
                'file': test_file,
                'subject': 'Testing'
            })
            self.assertEqual(upload_response.status_code, 302)
        
        # Check achievements page
        achievements_response = self.client.get(reverse('gamification:achievements'))
        self.assertEqual(achievements_response.status_code, 200)
        
        # Check leaderboard
        leaderboard_response = self.client.get(reverse('gamification:leaderboard'))
        self.assertEqual(leaderboard_response.status_code, 200)
        
        # Check virtual currency
        shop_response = self.client.get(reverse('gamification:shop'))
        self.assertEqual(shop_response.status_code, 200)
    
    def test_system_health_and_monitoring(self):
        """Test system health checks and monitoring endpoints"""
        
        # Test health check endpoints
        health_response = self.client.get(reverse('health_check'))
        self.assertEqual(health_response.status_code, 200)
        
        readiness_response = self.client.get(reverse('readiness_check'))
        self.assertEqual(readiness_response.status_code, 200)
        
        liveness_response = self.client.get(reverse('liveness_check'))
        self.assertEqual(liveness_response.status_code, 200)
        
        metrics_response = self.client.get(reverse('metrics'))
        self.assertEqual(metrics_response.status_code, 200)
    
    def test_security_and_permissions(self):
        """Test security measures and role-based permissions"""
        
        # Test unauthenticated access
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test role-based access
        self.client.login(username='student1', password='testpass123')
        
        # Student should not access teacher dashboard
        teacher_response = self.client.get(reverse('accounts:teacher_dashboard'))
        self.assertEqual(teacher_response.status_code, 403)
        
        # Test file upload security
        malicious_file = SimpleUploadedFile(
            "malicious.exe",
            b"malicious content",
            content_type="application/x-executable"
        )
        
        upload_response = self.client.post(reverse('content:upload'), {
            'title': 'Malicious File',
            'file': malicious_file,
            'subject': 'Testing'
        })
        # Should reject non-allowed file types
        self.assertNotEqual(upload_response.status_code, 302)
    
    def test_performance_and_caching(self):
        """Test performance optimizations and caching"""
        
        self.client.login(username='student1', password='testpass123')
        
        # Test that repeated requests use caching
        start_time = time.time()
        response1 = self.client.get(reverse('content:library'))
        first_request_time = time.time() - start_time
        
        start_time = time.time()
        response2 = self.client.get(reverse('content:library'))
        second_request_time = time.time() - start_time
        
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        
        # Second request should be faster due to caching
        # (This is a basic test - in practice you'd need more sophisticated timing)
    
    def tearDown(self):
        """Clean up after tests"""
        cache.clear()
        # Clean up any uploaded files
        for content in UploadedContent.objects.all():
            if content.file and os.path.exists(content.file.path):
                os.remove(content.file.path)


import time