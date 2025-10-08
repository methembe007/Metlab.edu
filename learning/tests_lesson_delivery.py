"""
Tests for the lesson delivery system functionality
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from accounts.models import StudentProfile
from .models import DailyLesson, LessonProgress
from .lesson_service import LessonDeliveryService
import json

User = get_user_model()


class LessonDeliveryServiceTest(TestCase):
    """Test cases for LessonDeliveryService"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='student'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            total_xp=0,
            current_streak=0
        )
        
        # Create a test lesson
        self.lesson = DailyLesson.objects.create(
            student=self.student_profile,
            lesson_date=timezone.now().date(),
            lesson_type='mixed',
            title='Test Lesson',
            description='A test lesson for validation',
            content_structure={
                'activities': [
                    {
                        'type': 'quiz',
                        'title': 'Test Quiz',
                        'concept': 'Math',
                        'questions': [
                            {
                                'text': 'What is 2+2?',
                                'options': [
                                    {'text': '3', 'is_correct': False},
                                    {'text': '4', 'is_correct': True},
                                    {'text': '5', 'is_correct': False}
                                ]
                            }
                        ]
                    },
                    {
                        'type': 'reflection',
                        'title': 'Reflection',
                        'concept': 'Learning',
                        'min_words': 10
                    }
                ]
            },
            estimated_duration_minutes=10,
            status='active'
        )
    
    def test_validate_lesson_completion_success(self):
        """Test successful lesson completion validation"""
        # Create progress entries for all activities
        LessonProgress.objects.create(
            lesson=self.lesson,
            activity_index=0,
            activity_type='quiz',
            concept='Math',
            student_answer='[{"question": "What is 2+2?", "answer": "4", "correct": true}]',
            is_correct=True,
            time_spent_seconds=60
        )
        
        LessonProgress.objects.create(
            lesson=self.lesson,
            activity_index=1,
            activity_type='reflection',
            concept='Learning',
            student_answer='This lesson helped me understand basic math concepts better and I learned how to solve problems step by step.',
            is_correct=True,
            time_spent_seconds=120
        )
        
        progress_entries = LessonProgress.objects.filter(lesson=self.lesson)
        is_valid, error_message = LessonDeliveryService.validate_lesson_completion(
            self.lesson, progress_entries
        )
        
        if not is_valid:
            print(f"Validation failed with error: {error_message}")
        
        self.assertTrue(is_valid, f"Validation failed: {error_message}")
        self.assertEqual(error_message, "")
    
    def test_validate_lesson_completion_missing_activities(self):
        """Test lesson completion validation with missing activities"""
        # Only create progress for first activity
        LessonProgress.objects.create(
            lesson=self.lesson,
            activity_index=0,
            activity_type='quiz',
            concept='Math',
            student_answer='[{"question": "What is 2+2?", "answer": "4", "correct": true}]',
            is_correct=True,
            time_spent_seconds=60
        )
        
        progress_entries = LessonProgress.objects.filter(lesson=self.lesson)
        is_valid, error_message = LessonDeliveryService.validate_lesson_completion(
            self.lesson, progress_entries
        )
        
        self.assertFalse(is_valid)
        self.assertIn("Missing progress for activities", error_message)
    
    def test_calculate_lesson_score(self):
        """Test lesson score calculation"""
        # Create progress entries
        LessonProgress.objects.create(
            lesson=self.lesson,
            activity_index=0,
            activity_type='quiz',
            concept='Math',
            student_answer='[{"question": "What is 2+2?", "answer": "4", "correct": true}]',
            is_correct=True,
            time_spent_seconds=60
        )
        
        LessonProgress.objects.create(
            lesson=self.lesson,
            activity_index=1,
            activity_type='reflection',
            concept='Learning',
            student_answer='This lesson helped me understand basic math concepts better.',
            is_correct=True,
            time_spent_seconds=120
        )
        
        progress_entries = LessonProgress.objects.filter(lesson=self.lesson)
        score = LessonDeliveryService.calculate_lesson_score(self.lesson, progress_entries)
        
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_calculate_xp_earned(self):
        """Test XP calculation"""
        performance_score = 85.0
        completion_ratio = 1.0
        
        xp = LessonDeliveryService.calculate_xp_earned(
            self.lesson, performance_score, completion_ratio
        )
        
        self.assertGreaterEqual(xp, 5)  # Minimum XP
        self.assertIsInstance(xp, int)
    
    def test_get_lesson_analytics(self):
        """Test lesson analytics generation"""
        # Create progress entries
        LessonProgress.objects.create(
            lesson=self.lesson,
            activity_index=0,
            activity_type='quiz',
            concept='Math',
            student_answer='[{"question": "What is 2+2?", "answer": "4", "correct": true}]',
            is_correct=True,
            time_spent_seconds=60,
            difficulty_rating='easy'
        )
        
        # Complete the lesson
        self.lesson.complete_lesson(performance_score=90.0, xp_earned=15)
        
        analytics = LessonDeliveryService.get_lesson_analytics(self.lesson)
        
        self.assertEqual(analytics['lesson_id'], self.lesson.id)
        self.assertEqual(analytics['performance_score'], 90.0)
        self.assertEqual(analytics['xp_earned'], 15)
        self.assertEqual(len(analytics['activities']), 1)
        self.assertIn('Math', analytics['concepts_covered'])
    
    def test_get_student_lesson_stats(self):
        """Test student lesson statistics"""
        # Complete the lesson
        self.lesson.complete_lesson(performance_score=85.0, xp_earned=12)
        
        stats = LessonDeliveryService.get_student_lesson_stats(self.student_profile)
        
        self.assertEqual(stats['total_lessons'], 1)
        self.assertEqual(stats['completed_lessons'], 1)
        self.assertEqual(stats['completion_rate'], 100.0)
        self.assertEqual(stats['average_score'], 85.0)
        self.assertEqual(stats['total_xp'], 12)


class LessonDeliveryViewTest(TestCase):
    """Test cases for lesson delivery views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='student'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            total_xp=0,
            current_streak=0
        )
        
        self.lesson = DailyLesson.objects.create(
            student=self.student_profile,
            lesson_date=timezone.now().date(),
            lesson_type='mixed',
            title='Test Lesson',
            description='A test lesson',
            content_structure={'activities': []},
            estimated_duration_minutes=10,
            status='scheduled'
        )
        
        self.client.login(username='testuser', password='testpass123')
    
    def test_start_daily_lesson(self):
        """Test starting a daily lesson"""
        url = reverse('learning:start_daily_lesson', args=[self.lesson.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Check lesson status updated
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.status, 'active')
    
    def test_record_lesson_progress(self):
        """Test recording lesson progress"""
        self.lesson.status = 'active'
        self.lesson.save()
        
        url = reverse('learning:record_lesson_progress', args=[self.lesson.id])
        data = {
            'activity_index': 0,
            'activity_type': 'quiz',
            'concept': 'Math',
            'student_answer': 'Test answer',
            'is_correct': True,
            'time_spent_seconds': 60
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Check progress was recorded
        progress = LessonProgress.objects.filter(lesson=self.lesson).first()
        self.assertIsNotNone(progress)
        self.assertEqual(progress.activity_index, 0)
        self.assertEqual(progress.concept, 'Math')
    
    def test_complete_daily_lesson(self):
        """Test completing a daily lesson"""
        self.lesson.status = 'active'
        self.lesson.save()
        
        # Create some progress first
        LessonProgress.objects.create(
            lesson=self.lesson,
            activity_index=0,
            activity_type='quiz',
            concept='Math',
            student_answer='Test answer',
            is_correct=True,
            time_spent_seconds=60
        )
        
        url = reverse('learning:complete_daily_lesson', args=[self.lesson.id])
        data = {
            'performance_score': 85.0,
            'xp_earned': 12
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Check lesson was completed
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.status, 'completed')
        self.assertEqual(self.lesson.performance_score, 85.0)
        self.assertEqual(self.lesson.xp_earned, 12)
    
    def test_lesson_history_view(self):
        """Test lesson history view"""
        url = reverse('learning:lesson_history')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lesson History')
        self.assertContains(response, self.lesson.title)
    
    def test_lesson_analytics_api(self):
        """Test lesson analytics API"""
        # Complete the lesson first
        self.lesson.complete_lesson(performance_score=90.0, xp_earned=15)
        
        url = reverse('learning:lesson_analytics', args=[self.lesson.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('analytics', data)
        self.assertEqual(data['analytics']['lesson_id'], self.lesson.id)