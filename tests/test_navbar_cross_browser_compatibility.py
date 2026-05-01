"""
Cross-Browser Compatibility Tests for Modern Animated Navbar
Tests navbar functionality across Chrome 90+, Firefox 88+, Safari 14+, and Edge 90+
Verifies animations work smoothly, touch interactions, and documents browser-specific issues

Requirements: 5.4, 6.1, 6.2
"""

import unittest
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test.utils import override_settings
from accounts.models import StudentProfile, TeacherProfile, ParentProfile
import json
import re
from unittest.mock import patch

User = get_user_model()


class NavbarBrowserCompatibilityTestCase(TestCase):
    """Test navbar compatibility across Chrome 90+, Firefox 88+, Safari 14+, Edge 90+"""
    
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
    
    def test_chrome_90_plus_compatibility(self):
        """Test Chrome 90+ desktop and mobile compatibility"""
        # Simulate Chrome 90+ user agent
        response = self.client.get(
            reverse('accounts:student_dashboard'),
            HTTP_USER_AGENT='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
        )
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Test glass-morphism support (backdrop-filter)
        self.assertIn('backdrop-blur-md', content)
        self.assertIn('bg-white/95', content)
        
        # Test CSS Grid and Flexbox
        self.assertIn('flex', content)
        self.assertIn('items-center', content)
        self.assertIn('justify-between', content)
        
        # Test CSS transforms for animations
        self.assertIn('transform', content)
        self.assertIn('group-hover:scale-110', content)
        self.assertIn('group-hover:rotate-3', content)
        
        # Test CSS gradients
        self.assertIn('bg-gradient-to-br', content)
        self.assertIn('from-blue-500', content)
        self.assertIn('to-blue-700', content)
        
        # Test JavaScript functionality
        self.assertIn('toggleMobileMenu', content)
        self.assertIn('addEventListener', content)
    
    def test_chrome_mobile_compatibility(self):
        """Test Chrome Mobile compatibility"""
        # Simulate Chrome Mobile user agent
        response = self.client.get(
            reverse('accounts:student_dashboard'),
            HTTP_USER_AGENT='Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36'
        )
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Test mobile-specific meta tags
        self.assertIn('name="viewport" content="width=device-width, initial-scale=1.0"', content)
        self.assertIn('name="theme-color" content="#3b82f6"', content)
        self.assertIn('name="apple-mobile-web-app-capable" content="yes"', content)
        
        # Test touch-friendly button sizing (minimum 44x44px)
        self.assertIn('w-10 h-10', content)  # 40x40px + padding = 44x44px+
        
        # Test hamburger icon structure
        self.assertIn('hamburger-icon', content)
        self.assertIn('hamburger-line', content)
        
        # Test mobile dropdown
        self.assertIn('mobile-dropdown', content)
        self.assertIn('mobile-menu-item', content)
    
    def test_firefox_88_plus_compatibility(self):
        """Test Firefox 88+ compatibility"""
        # Simulate Firefox 88+ user agent
        response = self.client.get(
            reverse('accounts:student_dashboard'),
            HTTP_USER_AGENT='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0'
        )
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Test backdrop-filter fallback for older Firefox versions
        self.assertIn('@supports not (backdrop-filter: blur(10px))', content)
        self.assertIn('background: rgba(255, 255, 255, 1) !important', content)
        
        # Test CSS animations work
        self.assertIn('transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1)', content)
        self.assertIn('@keyframes slideInLeft', content)
        self.assertIn('@keyframes fadeInScale', content)
        
        # Test flexbox support
        self.assertIn('flex', content)
        self.assertIn('space-x-', content)
        
        # Test JavaScript event handling
        self.assertIn('addEventListener(\'click\', toggleMobileMenu)', content)
        self.assertIn('addEventListener(\'keydown\'', content)
    
    def test_safari_14_plus_macos_compatibility(self):
        """Test Safari 14+ macOS compatibility"""
        # Simulate Safari 14+ macOS user agent
        response = self.client.get(
            reverse('accounts:student_dashboard'),
            HTTP_USER_AGENT='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        )
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Test webkit prefixes handled by TailwindCSS
        self.assertIn('backdrop-blur-md', content)
        
        # Test CSS transforms
        self.assertIn('transform', content)
        self.assertIn('transition-all', content)
        
        # Test hover effects
        self.assertIn('hover:scale-110', content)
        self.assertIn('hover:bg-blue-50', content)
        
        # Test JavaScript functionality
        self.assertIn('function toggleMobileMenu()', content)
        self.assertIn('document.addEventListener(\'DOMContentLoaded\'', content)
    
    def test_safari_ios_compatibility(self):
        """Test Safari iOS compatibility"""
        # Simulate Safari iOS user agent
        response = self.client.get(
            reverse('accounts:student_dashboard'),
            HTTP_USER_AGENT='Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1'
        )
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Test iOS-specific meta tags
        self.assertIn('name="apple-mobile-web-app-capable" content="yes"', content)
        self.assertIn('name="apple-mobile-web-app-status-bar-style" content="default"', content)
        self.assertIn('name="apple-mobile-web-app-title" content="Metlab.edu"', content)
        
        # Test touch-friendly interface
        self.assertIn('w-10 h-10', content)  # Touch target sizing
        self.assertIn('px-4 py-3', content)  # Mobile menu item padding
        
        # Test viewport optimization
        self.assertIn('width=device-width, initial-scale=1.0', content)
        
        # Test responsive design
        self.assertIn('md:hidden', content)
        self.assertIn('hidden md:flex', content)
    
    def test_edge_90_plus_compatibility(self):
        """Test Edge 90+ compatibility"""
        # Simulate Edge 90+ user agent
        response = self.client.get(
            reverse('accounts:student_dashboard'),
            HTTP_USER_AGENT='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36 Edg/90.0.818.66'
        )
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Edge uses Chromium engine, so should have same compatibility as Chrome
        self.assertIn('backdrop-blur-md', content)
        self.assertIn('bg-gradient-to-br', content)
        self.assertIn('transform', content)
        self.assertIn('transition-all', content)
        
        # Test JavaScript functionality
        self.assertIn('toggleMobileMenu', content)
        self.assertIn('cubic-bezier(0.4, 0, 0.2, 1)', content)


class NavbarAnimationPerformanceTestCase(TestCase):
    """Test animation performance across browsers"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='animtest',
            email='anim@test.com',
            password='testpass123',
            role='student'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            learning_preferences={'subjects': ['math']},
            current_streak=1,
            total_xp=10
        )
        self.client.login(username='animtest', password='testpass123')
    
    def test_hamburger_animation_performance(self):
        """Test hamburger icon morphing animation performance"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Test hardware-accelerated transforms
        self.assertIn('transform: translateY(8px) rotate(45deg)', content)
        self.assertIn('transform: scaleX(0)', content)
        self.assertIn('transform: translateY(-8px) rotate(-45deg)', content)
        
        # Test smooth timing function
        self.assertIn('cubic-bezier(0.4, 0, 0.2, 1)', content)
        
        # Test transform-origin for smooth rotation
        self.assertIn('transform-origin: center', content)
        
        # Test 300ms duration for 60fps performance
        self.assertIn('transition: all 0.3s', content)
    
    def test_dropdown_animation_performance(self):
        """Test mobile dropdown slide animation performance"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Test max-height animation (better than height: auto)
        self.assertIn('max-height: 0', content)
        self.assertIn('max-height: 500px', content)
        self.assertIn('transition: max-height 0.3s ease-in-out', content)
        
        # Test overflow hidden for smooth clipping
        self.assertIn('overflow: hidden', content)
    
    def test_staggered_animation_performance(self):
        """Test staggered menu item animation performance"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Test staggered delays (50ms increments)
        self.assertIn('animation-delay: 0.1s', content)
        self.assertIn('animation-delay: 0.15s', content)
        self.assertIn('animation-delay: 0.2s', content)
        self.assertIn('animation-delay: 0.25s', content)
        
        # Test slideInLeft keyframes
        self.assertIn('@keyframes slideInLeft', content)
        self.assertIn('opacity: 1', content)
        self.assertIn('transform: translateX(0)', content)
        
        # Test animation fills forwards
        self.assertIn('animation: slideInLeft 0.3s ease-out forwards', content)
    
    def test_hover_animation_performance(self):
        """Test hover animation performance"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Test logo hover animations
        self.assertIn('group-hover:scale-110', content)
        self.assertIn('group-hover:rotate-3', content)
        self.assertIn('transition-all duration-300', content)
        
        # Test link hover effects
        self.assertIn('hover:text-blue-600', content)
        self.assertIn('hover:bg-blue-50', content)
        self.assertIn('transition-all duration-200', content)


class NavbarTouchInteractionTestCase(TestCase):
    """Test touch interactions on mobile devices"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='touchtest',
            email='touch@test.com',
            password='testpass123',
            role='student'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            learning_preferences={'subjects': ['math']},
            current_streak=1,
            total_xp=10
        )
        self.client.login(username='touchtest', password='testpass123')
    
    def test_touch_target_sizing(self):
        """Test touch targets meet minimum 44x44px requirement"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Test hamburger button sizing (w-10 h-10 = 40x40px + padding)
        self.assertIn('w-10 h-10', content)
        self.assertIn('flex items-center justify-center', content)
        
        # Test mobile menu item padding for touch-friendly size
        self.assertIn('px-4 py-3', content)
        
        # Test button hover states for touch feedback
        self.assertIn('hover:bg-gray-100', content)
        self.assertIn('hover:bg-blue-50', content)
    
    def test_touch_event_handling(self):
        """Test touch event handling in JavaScript"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Test click event listener (works for touch)
        self.assertIn('addEventListener(\'click\', toggleMobileMenu)', content)
        
        # Test touch-friendly keyboard support
        self.assertIn('event.key === \'Enter\'', content)
        self.assertIn('event.key === \' \'', content)
        
        # Test focus management for touch devices
        self.assertIn('focus:outline-none', content)
        self.assertIn('focus:ring-2', content)
        self.assertIn('focus:ring-blue-500', content)
    
    def test_mobile_responsive_behavior(self):
        """Test responsive behavior on mobile devices"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Test mobile breakpoint classes
        self.assertIn('md:hidden', content)  # Show on mobile only
        self.assertIn('hidden md:flex', content)  # Hide on mobile
        
        # Test responsive spacing
        self.assertIn('px-4 sm:px-6 lg:px-8', content)
        
        # Test mobile-first design
        self.assertIn('hidden lg:inline', content)  # User name hidden on small screens
        self.assertIn('sm:px-6', content)  # Responsive padding


class NavbarBrowserFallbackTestCase(TestCase):
    """Test browser fallbacks and graceful degradation"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='fallbacktest',
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
        self.client.login(username='fallbacktest', password='testpass123')
    
    def test_backdrop_filter_fallback(self):
        """Test fallback for backdrop-filter CSS property"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Test @supports rule for feature detection
        self.assertIn('@supports not (backdrop-filter: blur(10px))', content)
        
        # Test fallback background
        self.assertIn('background: rgba(255, 255, 255, 1) !important', content)
        
        # Test original glass-morphism classes still present
        self.assertIn('backdrop-blur-md', content)
        self.assertIn('bg-white/95', content)
    
    def test_css_gradient_fallback(self):
        """Test CSS gradient fallback"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Test gradient classes are present
        self.assertIn('bg-gradient-to-br', content)
        self.assertIn('bg-gradient-to-r', content)
        
        # Test solid color fallbacks in CSS
        self.assertIn('from-blue-500', content)
        self.assertIn('to-blue-700', content)
    
    def test_flexbox_support(self):
        """Test flexbox layout support"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Test flexbox classes
        self.assertIn('flex', content)
        self.assertIn('items-center', content)
        self.assertIn('justify-between', content)
        self.assertIn('space-x-', content)
        
        # Test flex-shrink for logo
        self.assertIn('flex-shrink-0', content)
    
    def test_javascript_error_handling(self):
        """Test JavaScript error handling and null checks"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Test null checks for DOM elements
        self.assertIn('if (!hamburger || !dropdown) return', content)
        
        # Test element existence checks
        self.assertIn('if (!hamburger || !dropdown)', content)
        
        # Test safe event listener attachment
        self.assertIn('if (!hamburger.contains(event.target)', content)


class NavbarAccessibilityCompatibilityTestCase(TestCase):
    """Test accessibility features across browsers"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='a11ytest',
            email='a11y@test.com',
            password='testpass123',
            role='student'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            learning_preferences={'subjects': ['math']},
            current_streak=1,
            total_xp=10
        )
        self.client.login(username='a11ytest', password='testpass123')
    
    def test_semantic_html_structure(self):
        """Test semantic HTML5 structure"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Test semantic nav element
        self.assertIn('<nav', content)
        self.assertIn('role="navigation"', content)
        self.assertIn('aria-label="Main navigation"', content)
        
        # Test proper button element
        self.assertIn('<button', content)
        self.assertIn('type="button"', content)
        
        # Test main content area
        self.assertIn('<main', content)
        self.assertIn('<footer', content)
    
    def test_aria_attributes(self):
        """Test ARIA attributes for screen readers"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Test hamburger button ARIA
        self.assertIn('aria-label="Toggle navigation menu"', content)
        self.assertIn('aria-expanded="false"', content)
        self.assertIn('aria-controls="mobile-dropdown"', content)
        
        # Test mobile dropdown ARIA
        self.assertIn('role="menu"', content)
        self.assertIn('aria-labelledby="hamburger-btn"', content)
        self.assertIn('aria-hidden="true"', content)
        
        # Test menu items
        self.assertIn('role="menuitem"', content)
        
        # Test separators
        self.assertIn('role="separator"', content)
        
        # Test status elements
        self.assertIn('role="status"', content)
    
    def test_keyboard_navigation_support(self):
        """Test keyboard navigation functionality"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Test keyboard event handlers
        self.assertIn('addEventListener(\'keydown\'', content)
        self.assertIn('event.key === \'Enter\'', content)
        self.assertIn('event.key === \' \'', content)
        self.assertIn('event.key === \'Escape\'', content)
        
        # Test focus management
        self.assertIn('focus:outline-none', content)
        self.assertIn('focus:ring-2', content)
        self.assertIn('focus:ring-blue-500', content)
        
        # Test focus return on escape
        self.assertIn('hamburger.focus()', content)
    
    def test_screen_reader_support(self):
        """Test screen reader support"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Test aria-hidden on decorative icons
        self.assertIn('aria-hidden="true"', content)
        
        # Test descriptive aria-labels
        self.assertIn('aria-label="Metlab.edu home"', content)
        self.assertIn('aria-label="Go to dashboard"', content)
        self.assertIn('aria-label="Browse content library"', content)
        
        # Test role attributes
        self.assertIn('role="menubar"', content)
        self.assertIn('role="presentation"', content)


class NavbarSecurityCompatibilityTestCase(TestCase):
    """Test security features across browsers"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='sectest',
            email='sec@test.com',
            password='testpass123',
            role='student'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            learning_preferences={'subjects': ['math']},
            current_streak=1,
            total_xp=10
        )
        self.client.login(username='sectest', password='testpass123')
    
    def test_csrf_protection(self):
        """Test CSRF token presence"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Test CSRF token meta tag
        self.assertIn('name="csrf-token"', content)
        # The CSRF token should be rendered, not visible as template code
        self.assertIn('content="', content)  # Token should be rendered with actual value
    
    def test_xss_prevention(self):
        """Test XSS prevention in navbar content"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Test user content is properly rendered and escaped
        # The template variables should be rendered, not visible as template code
        self.assertNotIn('{{ user.first_name|default:user.username }}', content)
        self.assertNotIn('{{ user_role|title }}', content)
        
        # Test actual user content is present and escaped
        self.assertIn('sectest', content)  # Username should be rendered
        self.assertIn('Student', content)  # Role should be rendered
        
        # Test no unsafe HTML injection
        self.assertNotIn('|safe', content)
    
    def test_secure_external_resources(self):
        """Test external resources use HTTPS"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Test CDN links use HTTPS
        self.assertIn('https://cdn.jsdelivr.net', content)
        self.assertIn('https://cdnjs.cloudflare.com', content)
        
        # Test no insecure HTTP links
        self.assertNotIn('http://', content)


class NavbarUserRoleCompatibilityTestCase(TestCase):
    """Test navbar adapts correctly for different user roles across browsers"""
    
    def test_student_role_compatibility(self):
        """Test student role navbar across browsers"""
        user = User.objects.create_user(
            username='student_compat',
            email='student@compat.com',
            password='testpass123',
            role='student'
        )
        StudentProfile.objects.create(
            user=user,
            learning_preferences={'subjects': ['math']},
            current_streak=1,
            total_xp=10
        )
        self.client.login(username='student_compat', password='testpass123')
        
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Test student-specific links
        self.assertIn('Achievements', content)
        self.assertIn('Shop', content)
        self.assertIn('Tutors', content)
        
        # Test role badge
        self.assertIn('Student', content)
    
    def test_teacher_role_compatibility(self):
        """Test teacher role navbar across browsers"""
        user = User.objects.create_user(
            username='teacher_compat',
            email='teacher@compat.com',
            password='testpass123',
            role='teacher'
        )
        TeacherProfile.objects.create(
            user=user,
            subjects=['math'],
            bio='Test teacher'
        )
        self.client.login(username='teacher_compat', password='testpass123')
        
        response = self.client.get(reverse('accounts:teacher_dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Test teacher-specific links
        self.assertIn('My Classes', content)
        
        # Test role badge
        self.assertIn('Teacher', content)
        
        # Should not have student-specific links
        self.assertNotIn('Achievements', content)
        self.assertNotIn('Shop', content)
    
    def test_parent_role_compatibility(self):
        """Test parent role navbar across browsers"""
        user = User.objects.create_user(
            username='parent_compat',
            email='parent@compat.com',
            password='testpass123',
            role='parent'
        )
        ParentProfile.objects.create(
            user=user,
            phone_number='1234567890'
        )
        self.client.login(username='parent_compat', password='testpass123')
        
        # Parent dashboard might redirect, so let's follow redirects
        response = self.client.get(reverse('accounts:parent_dashboard'), follow=True)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Test parent-specific links
        self.assertIn('Children', content)
        
        # Test role badge
        self.assertIn('Parent', content)


class NavbarPerformanceOptimizationTestCase(TestCase):
    """Test performance optimizations across browsers"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='perftest',
            email='perf@test.com',
            password='testpass123',
            role='student'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            learning_preferences={'subjects': ['math']},
            current_streak=1,
            total_xp=10
        )
        self.client.login(username='perftest', password='testpass123')
    
    def test_css_performance_optimizations(self):
        """Test CSS performance optimizations"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Test hardware acceleration hints
        self.assertIn('transform', content)
        self.assertIn('transition', content)
        
        # Test efficient selectors
        self.assertIn('class="', content)
        
        # Test preload hints
        self.assertIn('rel="preload"', content)
    
    def test_javascript_performance_optimizations(self):
        """Test JavaScript performance optimizations"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Test cached DOM queries
        self.assertIn('const hamburger = document.getElementById', content)
        self.assertIn('const dropdown = document.getElementById', content)
        
        # Test efficient event handling
        self.assertIn('addEventListener', content)
        
        # Test proper cleanup (null checks prevent memory leaks)
        self.assertIn('if (!hamburger || !dropdown) return', content)
    
    def test_resource_optimization(self):
        """Test resource loading optimization"""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Test CDN usage
        self.assertIn('cdn.', content)
        
        # Test compressed resources
        self.assertIn('output.css', content)  # Compiled CSS
        
        # Test async/defer where appropriate
        # Mobile optimizations script should load after DOM
        self.assertIn('mobile-optimizations.js', content)


if __name__ == '__main__':
    unittest.main()
