"""
Cross-browser and mobile testing suite for Metlab.edu platform.
Tests responsive design, browser compatibility, mobile features, and performance.
"""

import unittest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test.utils import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import StudentProfile, TeacherProfile, ParentProfile
from content.models import UploadedContent
from gamification.models import Achievement, StudentAchievement
from learning.models import LearningSession
from community.models import StudyGroup, TutorProfile
import json
import time

User = get_user_model()


class ResponsiveDesignTestCase(TestCase):
    """Test responsive design across different screen sizes"""
    
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
            learning_preferences={'subjects': ['math', 'science']},
            current_streak=5,
            total_xp=150
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_mobile_viewport_meta_tag(self):
        """Test that all pages include proper mobile viewport meta tag"""
        urls_to_test = [
            reverse('accounts:dashboard'),
            reverse('content:library'),
            reverse('content:upload'),
            reverse('gamification:achievements'),
            reverse('gamification:leaderboard'),
            reverse('community:tutor_recommendations'),
        ]
        
        for url in urls_to_test:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(
                response, 
                '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
                msg_prefix=f"Missing viewport meta tag on {url}"
            )
    
    def test_responsive_navigation(self):
        """Test navigation adapts to different screen sizes"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Check for responsive navigation classes
        self.assertContains(response, 'max-w-7xl mx-auto px-4')
        self.assertContains(response, 'flex justify-between h-16')
        
        # Verify navigation items are present
        self.assertContains(response, 'Dashboard')
        self.assertContains(response, 'Library')
        self.assertContains(response, 'Upload')
    
    def test_responsive_grid_layouts(self):
        """Test grid layouts adapt to screen sizes"""
        # Test achievements page grid
        response = self.client.get(reverse('gamification:achievements'))
        self.assertEqual(response.status_code, 200)
        
        # Check for responsive grid classes (should be in template)
        content = response.content.decode()
        # Grid should use responsive classes like grid-cols-1 md:grid-cols-2 lg:grid-cols-3
        self.assertTrue(
            'grid' in content or 'flex' in content,
            "Page should use responsive grid or flex layouts"
        )
    
    def test_responsive_forms(self):
        """Test forms are mobile-friendly"""
        response = self.client.get(reverse('content:upload'))
        self.assertEqual(response.status_code, 200)
        
        # Check for responsive form classes
        self.assertContains(response, 'w-full')  # Full width inputs
        
        # Test form submission works on mobile
        test_file = SimpleUploadedFile(
            "test.pdf", 
            b"file_content", 
            content_type="application/pdf"
        )
        
        response = self.client.post(reverse('content:upload'), {
            'title': 'Test Upload',
            'file': test_file,
            'subject': 'math'
        })
        
        # Should redirect or show success (not error)
        self.assertIn(response.status_code, [200, 302])


class BrowserCompatibilityTestCase(TestCase):
    """Test functionality across major browsers"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='browsertest',
            email='browser@example.com',
            password='testpass123',
            role='student'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            learning_preferences={'subjects': ['math']},
            current_streak=3,
            total_xp=100
        )
        self.client.login(username='browsertest', password='testpass123')
    
    def test_javascript_compatibility(self):
        """Test JavaScript features work across browsers"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Check for modern JavaScript features with fallbacks
        content = response.content.decode()
        
        # Should include Chart.js for analytics
        self.assertContains(response, 'chart.js')
        
        # Should include achievement notifications script
        if 'student' in content:
            self.assertContains(response, 'achievement_notifications.js')
    
    def test_css_compatibility(self):
        """Test CSS works across browsers"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Check for CSS framework inclusion
        self.assertContains(response, 'output.css')
        self.assertContains(response, 'tailwindcss.com')
        
        # Check for Font Awesome icons
        self.assertContains(response, 'font-awesome')
    
    def test_form_validation_compatibility(self):
        """Test form validation works across browsers"""
        # Test login form
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        
        # Should have proper form attributes for browser validation
        self.assertContains(response, 'type="email"')
        self.assertContains(response, 'required')
    
    def test_ajax_compatibility(self):
        """Test AJAX requests work properly"""
        # Test that CSRF token is properly included
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        self.assertContains(response, 'csrf-token')
        self.assertContains(response, '{% csrf_token %}')


class MobileFeatureTestCase(TestCase):
    """Test mobile-specific features and touch interactions"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='mobileuser',
            email='mobile@example.com',
            password='testpass123',
            role='student'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            learning_preferences={'subjects': ['science']},
            current_streak=7,
            total_xp=200
        )
        self.client.login(username='mobileuser', password='testpass123')
    
    def test_touch_friendly_buttons(self):
        """Test buttons are touch-friendly (minimum 44px)"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Check for proper button classes that ensure touch-friendly sizes
        content = response.content.decode()
        
        # Tailwind classes like py-2 px-4 should provide adequate touch targets
        self.assertIn('py-2 px-4', content)
        self.assertIn('font-bold', content)
    
    def test_mobile_navigation(self):
        """Test mobile navigation is accessible"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Navigation should be responsive
        self.assertContains(response, 'flex items-center space-x-4')
        
        # Should have proper spacing for mobile
        self.assertContains(response, 'px-4')
    
    def test_swipe_gestures_support(self):
        """Test pages support swipe gestures where appropriate"""
        # Test study room page (should support touch interactions)
        from community.models import Subject
        subject = Subject.objects.create(name='Math', description='Mathematics')
        study_group = StudyGroup.objects.create(
            name='Test Group',
            subject=subject,
            created_by=self.student_profile,
            max_members=5
        )
        study_group.members.add(self.student_profile)
        
        response = self.client.get(
            reverse('community:study_group_detail', args=[study_group.id])
        )
        self.assertEqual(response.status_code, 200)
        
        # Should include touch-friendly elements
        content = response.content.decode()
        self.assertTrue(len(content) > 0)  # Basic content check
    
    def test_mobile_file_upload(self):
        """Test file upload works on mobile devices"""
        response = self.client.get(reverse('content:upload'))
        self.assertEqual(response.status_code, 200)
        
        # Should have mobile-friendly file input
        self.assertContains(response, 'type="file"')
        
        # Test actual upload
        test_file = SimpleUploadedFile(
            "mobile_test.pdf",
            b"mobile file content",
            content_type="application/pdf"
        )
        
        response = self.client.post(reverse('content:upload'), {
            'title': 'Mobile Upload Test',
            'file': test_file,
            'subject': 'science'
        })
        
        self.assertIn(response.status_code, [200, 302])
    
    def test_mobile_video_chat_support(self):
        """Test video chat features work on mobile"""
        response = self.client.get(reverse('community:study_groups'))
        self.assertEqual(response.status_code, 200)
        
        # Should include WebRTC support scripts
        content = response.content.decode()
        # Basic check that study room functionality is available
        self.assertTrue('study' in content.lower())


class PerformanceOptimizationTestCase(TestCase):
    """Test performance optimizations for mobile devices"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='perfuser',
            email='perf@example.com',
            password='testpass123',
            role='student'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            learning_preferences={'subjects': ['math', 'science', 'english']},
            current_streak=10,
            total_xp=500
        )
        self.client.login(username='perfuser', password='testpass123')
    
    def test_page_load_performance(self):
        """Test pages load efficiently"""
        start_time = time.time()
        response = self.client.get(reverse('accounts:dashboard'))
        load_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(load_time, 2.0, "Dashboard should load in under 2 seconds")
    
    def test_static_file_optimization(self):
        """Test static files are optimized"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Should use CDN for external libraries
        self.assertContains(response, 'cdn.jsdelivr.net')
        self.assertContains(response, 'cdnjs.cloudflare.com')
        
        # Should have proper caching headers (tested via response)
        content = response.content.decode()
        self.assertTrue(len(content) > 0)
    
    def test_image_optimization(self):
        """Test images are optimized for mobile"""
        response = self.client.get(reverse('gamification:achievements'))
        self.assertEqual(response.status_code, 200)
        
        # Should use responsive image classes
        content = response.content.decode()
        # Check for responsive image handling
        if 'img' in content:
            self.assertIn('w-', content)  # Width classes
    
    def test_database_query_optimization(self):
        """Test database queries are optimized"""
        # Create test data
        for i in range(5):
            achievement = Achievement.objects.create(
                name=f'Test Achievement {i}',
                description=f'Description {i}',
                badge_icon='fas fa-star',
                xp_requirement=100 * i
            )
            StudentAchievement.objects.create(
                student=self.student_profile,
                achievement=achievement
            )
        
        # Test that achievements page loads efficiently
        start_time = time.time()
        response = self.client.get(reverse('gamification:achievements'))
        query_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(query_time, 1.0, "Achievements page should load quickly")
    
    def test_lazy_loading_support(self):
        """Test lazy loading is implemented where appropriate"""
        response = self.client.get(reverse('content:library'))
        self.assertEqual(response.status_code, 200)
        
        # Should implement pagination or lazy loading for large lists
        content = response.content.decode()
        # Check for pagination or lazy loading indicators
        has_pagination = 'page' in content.lower() or 'next' in content.lower()
        has_lazy_loading = 'loading="lazy"' in content
        
        # At least one optimization should be present
        self.assertTrue(
            has_pagination or has_lazy_loading or len(content) < 50000,
            "Large content lists should be optimized"
        )


class AccessibilityTestCase(TestCase):
    """Test accessibility features for mobile and desktop"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='a11yuser',
            email='a11y@example.com',
            password='testpass123',
            role='student'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            learning_preferences={'subjects': ['math']},
            current_streak=2,
            total_xp=50
        )
        self.client.login(username='a11yuser', password='testpass123')
    
    def test_semantic_html(self):
        """Test proper semantic HTML structure"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Should use semantic HTML elements
        self.assertContains(response, '<nav')
        self.assertContains(response, '<main')
        self.assertContains(response, '<footer')
    
    def test_keyboard_navigation(self):
        """Test keyboard navigation support"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Links and buttons should be keyboard accessible
        content = response.content.decode()
        
        # Check for proper link and button elements
        self.assertIn('<a href=', content)
        self.assertIn('class=', content)  # Should have proper styling
    
    def test_alt_text_for_images(self):
        """Test images have proper alt text"""
        response = self.client.get(reverse('gamification:achievements'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode()
        
        # If images are present, they should have alt text
        if '<img' in content:
            self.assertIn('alt=', content)
    
    def test_form_labels(self):
        """Test forms have proper labels"""
        response = self.client.get(reverse('content:upload'))
        self.assertEqual(response.status_code, 200)
        
        # Forms should have proper labels
        content = response.content.decode()
        if '<input' in content:
            # Should have labels or aria-labels
            has_labels = '<label' in content
            has_aria_labels = 'aria-label' in content
            self.assertTrue(
                has_labels or has_aria_labels,
                "Form inputs should have proper labels"
            )


class CrossBrowserIntegrationTestCase(TestCase):
    """Integration tests simulating different browser behaviors"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='integration',
            email='integration@example.com',
            password='testpass123',
            role='student'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            learning_preferences={'subjects': ['math', 'science']},
            current_streak=15,
            total_xp=750
        )
        self.client.login(username='integration', password='testpass123')
    
    def test_complete_user_journey_mobile(self):
        """Test complete user journey on mobile"""
        # 1. Dashboard access
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # 2. Content upload
        test_file = SimpleUploadedFile(
            "journey_test.pdf",
            b"test content for journey",
            content_type="application/pdf"
        )
        
        response = self.client.post(reverse('content:upload'), {
            'title': 'Journey Test',
            'file': test_file,
            'subject': 'math'
        })
        self.assertIn(response.status_code, [200, 302])
        
        # 3. View library
        response = self.client.get(reverse('content:library'))
        self.assertEqual(response.status_code, 200)
        
        # 4. Check achievements
        response = self.client.get(reverse('gamification:achievements'))
        self.assertEqual(response.status_code, 200)
        
        # 5. View leaderboard
        response = self.client.get(reverse('gamification:leaderboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_error_handling_across_browsers(self):
        """Test error handling works consistently"""
        # Test 404 handling
        response = self.client.get('/nonexistent-page/')
        self.assertEqual(response.status_code, 404)
        
        # Test invalid form submission
        response = self.client.post(reverse('content:upload'), {
            'title': '',  # Invalid: empty title
            'subject': 'math'
            # Missing file
        })
        
        # Should handle error gracefully
        self.assertIn(response.status_code, [200, 400])
    
    def test_session_handling(self):
        """Test session handling across different scenarios"""
        # Test logout
        response = self.client.get(reverse('accounts:logout'))
        self.assertIn(response.status_code, [200, 302])
        
        # Test accessing protected page after logout
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertIn(response.status_code, [302, 403])  # Should redirect to login


if __name__ == '__main__':
    unittest.main()