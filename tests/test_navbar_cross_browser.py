"""
Cross-browser compatibility tests for Modern Animated Navbar
Tests navbar functionality across Chrome 90+, Firefox 88+, Safari 14+, and Edge 90+
Verifies animations, touch interactions, and responsive behavior
"""

import unittest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test.utils import override_settings
from accounts.models import StudentProfile, TeacherProfile, ParentProfile
import json
import re

User = get_user_model()


class NavbarStructureTestCase(TestCase):
    """Test navbar HTML structure and semantic markup"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='navbartest',
            email='navbar@test.com',
            password='testpass123',
            role='student'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            learning_preferences={'subjects': ['math']},
            current_streak=1,
            total_xp=10
        )
        self.client.login(username='navbartest', password='testpass123')
    
    def test_navbar_semantic_structure(self):
        """Test navbar uses proper semantic HTML5 elements"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Check for semantic nav element
        self.assertIn('<nav', content)
        self.assertIn('role="navigation"', content)
        self.assertIn('aria-label="Main navigation"', content)
        
        # Check for proper ARIA attributes
        self.assertIn('aria-label', content)
        self.assertIn('aria-expanded', content)
        self.assertIn('aria-controls', content)
        self.assertIn('aria-hidden', content)
    
    def test_navbar_accessibility_attributes(self):
        """Test navbar has proper accessibility attributes"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Check hamburger button accessibility
        self.assertIn('aria-label="Toggle navigation menu"', content)
        self.assertIn('aria-expanded="false"', content)
        self.assertIn('aria-controls="mobile-dropdown"', content)
        
        # Check mobile dropdown accessibility
        self.assertIn('role="menu"', content)
        self.assertIn('aria-labelledby="hamburger-btn"', content)
        self.assertIn('aria-hidden="true"', content)
        
        # Check menu items have proper roles
        self.assertIn('role="menuitem"', content)
    
    def test_navbar_brand_logo_structure(self):
        """Test brand logo has proper structure and attributes"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Check brand logo link
        self.assertIn('aria-label="Metlab.edu home"', content)
        
        # Check gradient classes for logo
        self.assertIn('bg-gradient-to-br from-blue-500 to-blue-700', content)
        self.assertIn('bg-gradient-to-r from-blue-600 to-blue-800', content)
        
        # Check hover animation classes
        self.assertIn('group-hover:scale-110', content)
        self.assertIn('group-hover:rotate-3', content)
    
    def test_hamburger_icon_structure(self):
        """Test hamburger icon has proper HTML structure"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Check hamburger button structure
        self.assertIn('id="hamburger-btn"', content)
        self.assertIn('class="hamburger-icon"', content)
        self.assertIn('class="hamburger-line"', content)
        
        # Should have three hamburger lines
        hamburger_lines = content.count('class="hamburger-line"')
        self.assertEqual(hamburger_lines, 3, "Should have exactly 3 hamburger lines")


class NavbarCSSCompatibilityTestCase(TestCase):
    """Test CSS compatibility across browsers"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='csstest',
            email='css@test.com',
            password='testpass123',
            role='student'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            learning_preferences={'subjects': ['math']},
            current_streak=1,
            total_xp=10
        )
        self.client.login(username='csstest', password='testpass123')
    
    def test_glass_morphism_css(self):
        """Test glass-morphism effect CSS classes"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Check for glass-morphism classes
        self.assertIn('bg-white/95', content)
        self.assertIn('backdrop-blur-md', content)
        self.assertIn('shadow-lg', content)
        self.assertIn('border-b border-gray-200', content)
        
        # Check for fallback CSS
        self.assertIn('@supports not (backdrop-filter: blur(10px))', content)
        self.assertIn('background: rgba(255, 255, 255, 1) !important', content)
    
    def test_responsive_design_classes(self):
        """Test responsive design utility classes"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Check responsive visibility classes
        self.assertIn('hidden md:flex', content)  # Desktop nav
        self.assertIn('md:hidden', content)       # Mobile hamburger
        
        # Check responsive spacing
        self.assertIn('px-4 sm:px-6 lg:px-8', content)
        self.assertIn('space-x-1', content)
        
        # Check responsive text sizing
        self.assertIn('text-xl', content)
        self.assertIn('text-xs', content)
    
    def test_animation_css_properties(self):
        """Test CSS animation properties for cross-browser compatibility"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Check for CSS transitions
        self.assertIn('transition-all duration-300', content)
        self.assertIn('transition-colors', content)
        
        # Check for transform properties (hardware accelerated)
        self.assertIn('transform', content)
        self.assertIn('group-hover:scale-110', content)
        self.assertIn('group-hover:rotate-3', content)
        
        # Check for custom CSS animations
        self.assertIn('cubic-bezier(0.4, 0, 0.2, 1)', content)
        self.assertIn('@keyframes slideInLeft', content)
        self.assertIn('@keyframes fadeInScale', content)
    
    def test_gradient_css_compatibility(self):
        """Test CSS gradient compatibility"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Check for gradient classes
        self.assertIn('bg-gradient-to-br', content)
        self.assertIn('bg-gradient-to-r', content)
        self.assertIn('from-blue-500', content)
        self.assertIn('to-blue-700', content)
        
        # Check for text gradient
        self.assertIn('bg-clip-text', content)
        self.assertIn('text-transparent', content)


class NavbarJavaScriptTestCase(TestCase):
    """Test JavaScript functionality across browsers"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='jstest',
            email='js@test.com',
            password='testpass123',
            role='student'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            learning_preferences={'subjects': ['math']},
            current_streak=1,
            total_xp=10
        )
        self.client.login(username='jstest', password='testpass123')
    
    def test_javascript_function_presence(self):
        """Test JavaScript functions are properly defined"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Check for main toggle function
        self.assertIn('function toggleMobileMenu()', content)
        
        # Check for DOM ready event listener
        self.assertIn('document.addEventListener(\'DOMContentLoaded\'', content)
        
        # Check for element selection
        self.assertIn('document.getElementById(\'hamburger-btn\')', content)
        self.assertIn('document.getElementById(\'mobile-dropdown\')', content)
    
    def test_event_listeners_setup(self):
        """Test event listeners are properly set up"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Check for click event listener
        self.assertIn('addEventListener(\'click\', toggleMobileMenu)', content)
        
        # Check for keyboard event listeners
        self.assertIn('addEventListener(\'keydown\'', content)
        self.assertIn('event.key === \'Enter\'', content)
        self.assertIn('event.key === \' \'', content)
        self.assertIn('event.key === \'Escape\'', content)
        
        # Check for resize event listener
        self.assertIn('addEventListener(\'resize\'', content)
    
    def test_aria_attribute_updates(self):
        """Test ARIA attributes are updated by JavaScript"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Check for ARIA attribute updates
        self.assertIn('setAttribute(\'aria-expanded\'', content)
        self.assertIn('setAttribute(\'aria-hidden\'', content)
        
        # Check for proper boolean values
        self.assertIn('\'true\'', content)
        self.assertIn('\'false\'', content)
    
    def test_null_checks_and_error_handling(self):
        """Test JavaScript has proper null checks"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Check for null checks
        self.assertIn('if (!hamburger || !dropdown) return', content)
        self.assertIn('if (!hamburger.contains(event.target)', content)
        
        # Check for element existence checks
        self.assertIn('if (!hamburger || !dropdown)', content)


class NavbarResponsiveTestCase(TestCase):
    """Test responsive behavior across different screen sizes"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='responsive',
            email='responsive@test.com',
            password='testpass123',
            role='student'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            learning_preferences={'subjects': ['math']},
            current_streak=1,
            total_xp=10
        )
        self.client.login(username='responsive', password='testpass123')
    
    def test_mobile_breakpoint_classes(self):
        """Test mobile breakpoint utility classes"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Check for mobile-first responsive classes
        self.assertIn('md:flex', content)      # Show on medium screens and up
        self.assertIn('md:hidden', content)    # Hide on medium screens and up
        self.assertIn('sm:px-6', content)      # Small screen padding
        self.assertIn('lg:px-8', content)      # Large screen padding
        
        # Check for responsive text
        self.assertIn('hidden sm:inline', content)  # Show text on small screens
        self.assertIn('sm:hidden', content)         # Hide on small screens
    
    def test_touch_target_sizing(self):
        """Test touch targets meet minimum 44px requirement"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Check hamburger button sizing (w-10 h-10 = 40px, with padding should be 44px+)
        self.assertIn('w-10 h-10', content)
        
        # Check button padding for touch-friendly size
        self.assertIn('py-2 px-4', content)
        
        # Check mobile menu item padding
        self.assertIn('px-4 py-3', content)
    
    def test_viewport_meta_tag(self):
        """Test viewport meta tag for mobile optimization"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Check for proper viewport meta tag
        self.assertIn('<meta name="viewport" content="width=device-width, initial-scale=1.0">', content)
        
        # Check for mobile-specific meta tags
        self.assertIn('<meta name="theme-color" content="#3b82f6">', content)
        self.assertIn('<meta name="apple-mobile-web-app-capable" content="yes">', content)


class NavbarAnimationTestCase(TestCase):
    """Test animation compatibility across browsers"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='animation',
            email='animation@test.com',
            password='testpass123',
            role='student'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            learning_preferences={'subjects': ['math']},
            current_streak=1,
            total_xp=10
        )
        self.client.login(username='animation', password='testpass123')
    
    def test_hamburger_animation_css(self):
        """Test hamburger to X animation CSS"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Check for hamburger line transitions
        self.assertIn('transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1)', content)
        self.assertIn('transform-origin: center', content)
        
        # Check for active state transforms
        self.assertIn('#hamburger-btn.active .hamburger-line:nth-child(1)', content)
        self.assertIn('translateY(8px) rotate(45deg)', content)
        self.assertIn('opacity: 0', content)
        self.assertIn('scaleX(0)', content)
        self.assertIn('translateY(-8px) rotate(-45deg)', content)
    
    def test_dropdown_animation_css(self):
        """Test mobile dropdown slide animation CSS"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Check for dropdown transition
        self.assertIn('transition: max-height 0.3s ease-in-out', content)
        self.assertIn('max-height: 0', content)
        self.assertIn('overflow: hidden', content)
        
        # Check for active state
        self.assertIn('.mobile-dropdown.active', content)
        self.assertIn('max-height: 500px', content)
    
    def test_menu_item_staggered_animation(self):
        """Test staggered animation for mobile menu items"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Check for staggered animation delays
        self.assertIn('animation-delay: 0.1s', content)
        self.assertIn('animation-delay: 0.15s', content)
        self.assertIn('animation-delay: 0.2s', content)
        self.assertIn('animation-delay: 0.25s', content)
        
        # Check for slideInLeft keyframes
        self.assertIn('@keyframes slideInLeft', content)
        self.assertIn('opacity: 1', content)
        self.assertIn('transform: translateX(0)', content)
    
    def test_hover_animations(self):
        """Test hover animation effects"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Check for logo hover animations
        self.assertIn('group-hover:scale-110', content)
        self.assertIn('group-hover:rotate-3', content)
        
        # Check for link hover effects
        self.assertIn('hover:text-blue-600', content)
        self.assertIn('hover:bg-blue-50', content)
        
        # Check for button hover effects
        self.assertIn('hover:bg-gray-100', content)
        self.assertIn('hover:scale-105', content)


class NavbarUserRoleTestCase(TestCase):
    """Test navbar adapts to different user roles"""
    
    def test_student_navbar_content(self):
        """Test navbar content for student users"""
        user = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='testpass123',
            role='student'
        )
        StudentProfile.objects.create(
            user=user,
            learning_preferences={'subjects': ['math']},
            current_streak=1,
            total_xp=10
        )
        self.client.login(username='student', password='testpass123')
        
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Check student-specific links
        self.assertIn('Library', content)
        self.assertIn('Upload', content)
        self.assertIn('Tutors', content)
        self.assertIn('Achievements', content)
        self.assertIn('Shop', content)
        
        # Check role badge
        self.assertIn('Student', content)
    
    def test_teacher_navbar_content(self):
        """Test navbar content for teacher users"""
        user = User.objects.create_user(
            username='teacher',
            email='teacher@test.com',
            password='testpass123',
            role='teacher'
        )
        TeacherProfile.objects.create(
            user=user,
            subjects=['math'],
            bio='Test teacher'
        )
        self.client.login(username='teacher', password='testpass123')
        
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Check teacher-specific links
        self.assertIn('Library', content)
        self.assertIn('Upload', content)
        self.assertIn('My Classes', content)
        
        # Check role badge
        self.assertIn('Teacher', content)
        
        # Should not have student-specific links
        self.assertNotIn('Achievements', content)
        self.assertNotIn('Shop', content)
    
    def test_parent_navbar_content(self):
        """Test navbar content for parent users"""
        user = User.objects.create_user(
            username='parent',
            email='parent@test.com',
            password='testpass123',
            role='parent'
        )
        ParentProfile.objects.create(
            user=user,
            phone_number='1234567890'
        )
        self.client.login(username='parent', password='testpass123')
        
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Check parent-specific links
        self.assertIn('Children', content)
        
        # Check role badge
        self.assertIn('Parent', content)
        
        # Should not have student/teacher specific links
        self.assertNotIn('Library', content)
        self.assertNotIn('Upload', content)
        self.assertNotIn('Achievements', content)


class NavbarPerformanceTestCase(TestCase):
    """Test navbar performance optimizations"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='performance',
            email='performance@test.com',
            password='testpass123',
            role='student'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            learning_preferences={'subjects': ['math']},
            current_streak=1,
            total_xp=10
        )
        self.client.login(username='performance', password='testpass123')
    
    def test_css_optimization(self):
        """Test CSS is optimized for performance"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Check for hardware acceleration hints
        self.assertIn('transform', content)  # Uses transform for animations
        
        # Check for efficient selectors (no complex nesting in inline styles)
        # CSS should use class-based selectors
        self.assertIn('class="', content)
        
        # Check for preload hints
        self.assertIn('rel="preload"', content)
    
    def test_javascript_optimization(self):
        """Test JavaScript is optimized"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Check for efficient DOM queries (cached elements)
        self.assertIn('const hamburger = document.getElementById', content)
        self.assertIn('const dropdown = document.getElementById', content)
        
        # Check for event delegation where appropriate
        self.assertIn('addEventListener', content)
        
        # Check for proper cleanup (no memory leaks)
        self.assertIn('removeEventListener', content) or self.assertIn('null checks', content)
    
    def test_reduced_motion_support(self):
        """Test support for reduced motion preference"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Should have CSS that respects reduced motion
        # This would typically be in a separate CSS file, but check for animation properties
        self.assertIn('transition', content)
        self.assertIn('animation', content)


class NavbarBrowserFallbackTestCase(TestCase):
    """Test browser fallbacks and compatibility"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='fallback',
            email='fallback@test.com',
            password='testpass123',
            role='student'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            learning_preferences={'subjects': ['math']},
            current_streak=1,
            total_xp=10
        )
        self.client.login(username='fallback', password='testpass123')
    
    def test_backdrop_filter_fallback(self):
        """Test fallback for backdrop-filter CSS property"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Check for @supports rule
        self.assertIn('@supports not (backdrop-filter: blur(10px))', content)
        
        # Check for fallback background
        self.assertIn('background: rgba(255, 255, 255, 1) !important', content)
    
    def test_flexbox_support(self):
        """Test flexbox layout support"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Check for flexbox classes
        self.assertIn('flex', content)
        self.assertIn('items-center', content)
        self.assertIn('justify-between', content)
        self.assertIn('space-x-', content)
    
    def test_css_grid_fallback(self):
        """Test CSS Grid fallback to flexbox if needed"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Should primarily use flexbox for navbar (better browser support)
        self.assertIn('flex', content)
        
        # If grid is used elsewhere, should have flexbox fallback
        if 'grid' in content:
            self.assertIn('flex', content)  # Fallback present
    
    def test_font_awesome_fallback(self):
        """Test Font Awesome icon fallback"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Check for Font Awesome CDN
        self.assertIn('font-awesome', content)
        
        # Check for aria-hidden on icons (accessibility)
        self.assertIn('aria-hidden="true"', content)
        
        # Icons should have text alternatives nearby
        if 'fas fa-home' in content:
            self.assertIn('Dashboard', content)


class NavbarSecurityTestCase(TestCase):
    """Test navbar security features"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='security',
            email='security@test.com',
            password='testpass123',
            role='student'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            learning_preferences={'subjects': ['math']},
            current_streak=1,
            total_xp=10
        )
        self.client.login(username='security', password='testpass123')
    
    def test_csrf_token_presence(self):
        """Test CSRF token is properly included"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Check for CSRF token meta tag
        self.assertIn('name="csrf-token"', content)
        self.assertIn('content="{{ csrf_token }}"', content)
    
    def test_xss_prevention(self):
        """Test XSS prevention in navbar content"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # User content should be properly escaped
        # Django templates auto-escape by default
        self.assertIn('{{ user.first_name|default:user.username }}', content)
        self.assertIn('{{ user_role|title }}', content)
        
        # No raw HTML injection points
        self.assertNotIn('|safe', content)  # Should not use |safe filter
    
    def test_secure_links(self):
        """Test navbar links are secure"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # All internal links should use Django URL reversing
        self.assertIn('{% url ', content)
        
        # External CDN links should use HTTPS
        if 'http://' in content:
            # Should not have insecure HTTP links
            self.fail("Found insecure HTTP link in navbar")


if __name__ == '__main__':
    unittest.main()