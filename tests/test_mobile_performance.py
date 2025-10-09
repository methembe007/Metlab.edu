"""
Mobile performance testing script for Metlab.edu
Tests key mobile optimizations and performance metrics
"""

import unittest
import time
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from accounts.models import StudentProfile

User = get_user_model()


class MobilePerformanceTestCase(TestCase):
    """Test mobile performance optimizations"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='mobiletest',
            email='mobile@test.com',
            password='testpass123',
            role='student'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            learning_preferences={'subjects': ['math']},
            current_streak=1,
            total_xp=10
        )
        self.client.login(username='mobiletest', password='testpass123')
    
    def test_mobile_viewport_meta_tag(self):
        """Test that pages include mobile viewport meta tag"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, 
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        )
    
    def test_mobile_css_inclusion(self):
        """Test that mobile CSS is included"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'mobile-optimizations.css')
    
    def test_mobile_js_inclusion(self):
        """Test that mobile JavaScript is included"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'mobile-optimizations.js')
    
    def test_touch_friendly_navigation(self):
        """Test that navigation includes touch-friendly classes"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'touch-target')
    
    def test_responsive_grid_classes(self):
        """Test that responsive grid classes are present"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Check for responsive grid classes
        content = response.content.decode()
        responsive_classes = [
            'grid-cols-1',
            'md:grid-cols-2',
            'lg:grid-cols-3',
            'max-w-7xl',
            'mx-auto',
            'px-4'
        ]
        
        for css_class in responsive_classes:
            self.assertIn(css_class, content, f"Missing responsive class: {css_class}")
    
    def test_mobile_form_optimization(self):
        """Test that forms are optimized for mobile"""
        response = self.client.get(reverse('content:upload'))
        self.assertEqual(response.status_code, 200)
        
        # Check for mobile-friendly form attributes
        self.assertContains(response, 'w-full')  # Full width inputs
        
        # Check for proper input types
        content = response.content.decode()
        self.assertIn('type="file"', content)
    
    def test_page_load_performance(self):
        """Test that pages load within acceptable time"""
        start_time = time.time()
        response = self.client.get(reverse('accounts:student_dashboard'))
        load_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(load_time, 2.0, "Page should load in under 2 seconds")
    
    def test_cdn_resources(self):
        """Test that CDN resources are properly included"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Check for CDN resources
        self.assertContains(response, 'cdn.jsdelivr.net')
        self.assertContains(response, 'cdnjs.cloudflare.com')
    
    def test_mobile_meta_tags(self):
        """Test that mobile-specific meta tags are present"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Check for mobile meta tags
        self.assertContains(response, 'name="theme-color"')
        self.assertContains(response, 'name="apple-mobile-web-app-capable"')
        self.assertContains(response, 'name="apple-mobile-web-app-status-bar-style"')
    
    def test_semantic_html_structure(self):
        """Test that pages use semantic HTML"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Check for semantic HTML elements
        self.assertContains(response, '<nav')
        self.assertContains(response, '<main')
        self.assertContains(response, '<footer')
    
    def test_accessibility_features(self):
        """Test basic accessibility features"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode()
        
        # Check for proper heading structure
        self.assertIn('<h1', content)
        
        # Check for proper link structure
        self.assertIn('<a href=', content)


if __name__ == '__main__':
    unittest.main()