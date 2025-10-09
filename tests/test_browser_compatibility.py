"""
Browser compatibility testing for Metlab.edu
Tests cross-browser functionality and compatibility
"""

import unittest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import StudentProfile

User = get_user_model()


class BrowserCompatibilityTestCase(TestCase):
    """Test browser compatibility features"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='browsertest',
            email='browser@test.com',
            password='testpass123',
            role='student'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            learning_preferences={'subjects': ['math']},
            current_streak=1,
            total_xp=10
        )
        self.client.login(username='browsertest', password='testpass123')
    
    def test_css_framework_inclusion(self):
        """Test that CSS frameworks are properly included"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Check for TailwindCSS
        self.assertContains(response, 'tailwindcss.com')
        
        # Check for Font Awesome
        self.assertContains(response, 'font-awesome')
        
        # Check for custom CSS
        self.assertContains(response, 'output.css')
    
    def test_javascript_compatibility(self):
        """Test JavaScript compatibility features"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Check for Chart.js
        self.assertContains(response, 'chart.js')
        
        # Check for mobile optimizations script
        self.assertContains(response, 'mobile-optimizations.js')
    
    def test_form_validation_attributes(self):
        """Test that forms have proper validation attributes"""
        # Logout first to access login form
        self.client.logout()
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        
        # Check for HTML5 form validation attributes
        content = response.content.decode()
        
        # Should have proper input types (text or email)
        has_input_types = 'type="text"' in content or 'type="email"' in content or 'type="password"' in content
        self.assertTrue(has_input_types, "Should have proper input types")
        
        # Should have required attributes
        self.assertIn('required', content)
    
    def test_csrf_token_inclusion(self):
        """Test that CSRF tokens are properly included"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Check for CSRF token in meta tag
        self.assertContains(response, 'csrf-token')
        
        # Check for CSRF token in forms (rendered as input)
        self.assertContains(response, 'csrfmiddlewaretoken')
    
    def test_responsive_design_classes(self):
        """Test that responsive design classes are present"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode()
        
        # Check for responsive utility classes
        responsive_classes = [
            'max-w-7xl',
            'mx-auto',
            'px-4',
            'sm:px-6',
            'lg:px-8',
            'grid',
            'md:grid-cols-2',
            'lg:grid-cols-3'
        ]
        
        found_classes = []
        for css_class in responsive_classes:
            if css_class in content:
                found_classes.append(css_class)
        
        # Should have at least some responsive classes
        self.assertGreater(len(found_classes), 0, "Should have responsive design classes")
    
    def test_file_upload_compatibility(self):
        """Test file upload functionality across browsers"""
        response = self.client.get(reverse('content:upload'))
        self.assertEqual(response.status_code, 200)
        
        # Check for proper file input
        self.assertContains(response, 'type="file"')
        
        # Test file upload
        test_file = SimpleUploadedFile(
            "test.pdf",
            b"test content",
            content_type="application/pdf"
        )
        
        # This should not cause a server error
        response = self.client.post(reverse('content:upload'), {
            'file': test_file,
            'subject': 'math'
        })
        
        # Should either succeed or show validation errors, not crash
        self.assertIn(response.status_code, [200, 302, 400])
    
    def test_ajax_compatibility(self):
        """Test AJAX compatibility features"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Check that CSRF token is available for AJAX
        self.assertContains(response, 'name="csrf-token"')
    
    def test_icon_font_compatibility(self):
        """Test that icon fonts are properly loaded"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Check for Font Awesome icons
        content = response.content.decode()
        
        # Should have Font Awesome classes
        fa_classes = ['fas', 'far', 'fab', 'fa-']
        found_icons = any(fa_class in content for fa_class in fa_classes)
        
        if found_icons:
            # If icons are used, Font Awesome should be loaded
            self.assertContains(response, 'font-awesome')
    
    def test_progressive_enhancement(self):
        """Test progressive enhancement features"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode()
        
        # Should work without JavaScript (basic functionality)
        # Check for proper form actions
        if '<form' in content:
            self.assertIn('action=', content)
        
        # Should have proper fallbacks
        # Links should have proper href attributes
        if '<a' in content:
            self.assertIn('href=', content)
    
    def test_semantic_html_structure(self):
        """Test semantic HTML structure for accessibility"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Check for semantic HTML5 elements
        semantic_elements = ['<nav', '<main', '<footer', '<header', '<section', '<article']
        content = response.content.decode()
        
        found_elements = [elem for elem in semantic_elements if elem in content]
        
        # Should have at least nav, main, and footer
        required_elements = ['<nav', '<main', '<footer']
        for elem in required_elements:
            self.assertIn(elem, content, f"Missing semantic element: {elem}")
    
    def test_error_handling(self):
        """Test error handling across browsers"""
        # Test 404 handling
        response = self.client.get('/nonexistent-page/')
        self.assertEqual(response.status_code, 404)
        
        # Test invalid form submission
        response = self.client.post(reverse('content:upload'), {
            'subject': 'math'
            # Missing required file
        })
        
        # Should handle error gracefully
        self.assertIn(response.status_code, [200, 400])
    
    def test_performance_optimizations(self):
        """Test performance optimization features"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Check for CDN usage
        self.assertContains(response, 'cdn.')
        
        # Check for preload hints
        content = response.content.decode()
        if 'preload' in content:
            self.assertIn('rel="preload"', content)


if __name__ == '__main__':
    unittest.main()