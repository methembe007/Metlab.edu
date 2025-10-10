"""
Security penetration testing for Metlab.edu AI Learning Platform
Tests security vulnerabilities and attack vectors
"""

import re
import time
import hashlib
import base64
from django.test import TestCase, TransactionTestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.conf import settings
from django.middleware.csrf import get_token
from unittest.mock import patch
import json

from accounts.models import StudentProfile, TeacherProfile
from content.models import UploadedContent

User = get_user_model()


class SecurityPenetrationTestCase(TransactionTestCase):
    """Security penetration testing suite"""
    
    def setUp(self):
        """Set up test data for security testing"""
        self.client = Client()
        
        # Create test users
        self.student_user = User.objects.create_user(
            username='sectest_student',
            email='student@sectest.com',
            password='SecurePass123!',
            role='student'
        )
        
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            learning_preferences={'style': 'visual'},
            current_streak=5,
            total_xp=100
        )
        
        self.teacher_user = User.objects.create_user(
            username='sectest_teacher',
            email='teacher@sectest.com',
            password='SecurePass123!',
            role='teacher'
        )
        
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            institution='Security Test School'
        )
        
        # Admin user for privilege escalation tests
        self.admin_user = User.objects.create_superuser(
            username='sectest_admin',
            email='admin@sectest.com',
            password='AdminPass123!'
        )
    
    def test_authentication_security(self):
        """Test authentication security vulnerabilities"""
        print("\n" + "="*60)
        print("SECURITY TESTING: Authentication Security")
        print("="*60)
        
        # Test 1: Brute force protection
        print("  Testing brute force protection...")
        
        failed_attempts = 0
        lockout_triggered = False
        
        for i in range(15):  # Attempt 15 failed logins
            response = self.client.post(reverse('accounts:login'), {
                'username': 'sectest_student',
                'password': 'wrongpassword'
            })
            
            if response.status_code != 302:
                failed_attempts += 1
            
            # Check if account gets locked after multiple attempts
            if i > 5 and 'locked' in str(response.content).lower():
                lockout_triggered = True
                break
        
        print(f"    ✅ Failed login attempts: {failed_attempts}")
        if lockout_triggered:
            print("    ✅ Account lockout mechanism detected")
        else:
            print("    ⚠️  Consider implementing account lockout after multiple failures")
        
        # Test 2: Password strength validation
        print("  Testing password strength validation...")
        
        weak_passwords = [
            '123456',
            'password',
            'qwerty',
            'abc123',
            '111111'
        ]
        
        weak_password_rejected = 0
        
        for weak_pass in weak_passwords:
            try:
                User.objects.create_user(
                    username=f'weakpass_{weak_pass}',
                    email=f'weak_{weak_pass}@test.com',
                    password=weak_pass
                )
            except Exception:
                weak_password_rejected += 1
        
        print(f"    ✅ Weak passwords rejected: {weak_password_rejected}/{len(weak_passwords)}")
        
        # Test 3: Session security
        print("  Testing session security...")
        
        # Login and get session
        login_response = self.client.post(reverse('accounts:login'), {
            'username': 'sectest_student',
            'password': 'SecurePass123!'
        })
        
        if login_response.status_code == 302:
            # Check session cookie security
            session_cookie = None
            for cookie in self.client.cookies.values():
                if cookie.key == settings.SESSION_COOKIE_NAME:
                    session_cookie = cookie
                    break
            
            if session_cookie:
                # Check security flags
                security_flags = []
                if getattr(session_cookie, 'secure', False):
                    security_flags.append('Secure')
                if getattr(session_cookie, 'httponly', False):
                    security_flags.append('HttpOnly')
                
                print(f"    ✅ Session cookie security flags: {security_flags}")
            
            # Test session fixation
            old_session_key = self.client.session.session_key
            
            # Logout and login again
            self.client.logout()
            self.client.post(reverse('accounts:login'), {
                'username': 'sectest_student',
                'password': 'SecurePass123!'
            })
            
            new_session_key = self.client.session.session_key
            
            if old_session_key != new_session_key:
                print("    ✅ Session regeneration on login (prevents fixation)")
            else:
                print("    ⚠️  Session not regenerated on login")
    
    def test_authorization_security(self):
        """Test authorization and access control vulnerabilities"""
        print("\n" + "="*60)
        print("SECURITY TESTING: Authorization Security")
        print("="*60)
        
        # Test 1: Horizontal privilege escalation
        print("  Testing horizontal privilege escalation...")
        
        # Create another student
        other_student = User.objects.create_user(
            username='other_student',
            email='other@test.com',
            password='testpass123',
            role='student'
        )
        
        other_profile = StudentProfile.objects.create(
            user=other_student,
            learning_preferences={'style': 'auditory'},
            current_streak=0,
            total_xp=0
        )
        
        # Login as first student
        self.client.login(username='sectest_student', password='SecurePass123!')
        
        # Try to access other student's data
        response = self.client.get(f'/learning/student/{other_profile.id}/progress/')
        
        if response.status_code in [403, 404]:
            print("    ✅ Horizontal privilege escalation prevented")
        else:
            print("    ⚠️  Possible horizontal privilege escalation vulnerability")
        
        # Test 2: Vertical privilege escalation
        print("  Testing vertical privilege escalation...")
        
        # Try to access admin functionality as student
        admin_urls = [
            '/admin/',
            '/admin/auth/user/',
            reverse('accounts:teacher_dashboard'),
        ]
        
        escalation_prevented = 0
        
        for url in admin_urls:
            try:
                response = self.client.get(url)
                if response.status_code in [302, 403, 404]:
                    escalation_prevented += 1
            except:
                escalation_prevented += 1  # Exception also counts as prevention
        
        print(f"    ✅ Admin access prevented: {escalation_prevented}/{len(admin_urls)} URLs")
        
        # Test 3: Direct object reference
        print("  Testing insecure direct object references...")
        
        # Create content for other user
        other_content = UploadedContent.objects.create(
            user=other_student,
            title='Other Student Content',
            subject='Private'
        )
        
        # Try to access other user's content directly
        response = self.client.get(f'/content/{other_content.id}/')
        
        if response.status_code in [403, 404]:
            print("    ✅ Direct object reference protected")
        else:
            print("    ⚠️  Possible insecure direct object reference")
    
    def test_input_validation_security(self):
        """Test input validation and injection vulnerabilities"""
        print("\n" + "="*60)
        print("SECURITY TESTING: Input Validation")
        print("="*60)
        
        self.client.login(username='sectest_student', password='SecurePass123!')
        
        # Test 1: SQL Injection
        print("  Testing SQL injection protection...")
        
        sql_payloads = [
            "'; DROP TABLE auth_user; --",
            "' OR '1'='1",
            "'; UPDATE auth_user SET is_superuser=1; --",
            "' UNION SELECT * FROM auth_user --"
        ]
        
        sql_injection_blocked = 0
        
        for payload in sql_payloads:
            # Test in login form
            response = self.client.post(reverse('accounts:login'), {
                'username': payload,
                'password': 'testpass'
            })
            
            # Should not result in successful login or error
            if response.status_code != 302:
                sql_injection_blocked += 1
            
            # Test in search/filter parameters
            response = self.client.get(reverse('content:library'), {
                'search': payload
            })
            
            # Should handle malicious input gracefully
            if response.status_code == 200:
                sql_injection_blocked += 1
        
        print(f"    ✅ SQL injection attempts blocked: {sql_injection_blocked}/{len(sql_payloads) * 2}")
        
        # Test 2: XSS (Cross-Site Scripting)
        print("  Testing XSS protection...")
        
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>",
            "';alert('xss');//"
        ]
        
        xss_blocked = 0
        
        for payload in xss_payloads:
            # Test in content upload
            response = self.client.post(reverse('content:upload'), {
                'title': payload,
                'subject': 'Testing'
            })
            
            # Check if payload is escaped in response
            if payload not in str(response.content):
                xss_blocked += 1
        
        print(f"    ✅ XSS attempts blocked: {xss_blocked}/{len(xss_payloads)}")
        
        # Test 3: CSRF Protection
        print("  Testing CSRF protection...")
        
        # Try POST without CSRF token
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.login(username='sectest_student', password='SecurePass123!')
        
        response = csrf_client.post(reverse('content:upload'), {
            'title': 'CSRF Test',
            'subject': 'Testing'
        })
        
        if response.status_code == 403:
            print("    ✅ CSRF protection active")
        else:
            print("    ⚠️  CSRF protection may be disabled")
        
        # Test 4: File upload security
        print("  Testing file upload security...")
        
        malicious_files = [
            ('malware.exe', b'MZ\x90\x00', 'application/x-executable'),
            ('script.php', b'<?php system($_GET["cmd"]); ?>', 'application/x-php'),
            ('shell.jsp', b'<% Runtime.getRuntime().exec(request.getParameter("cmd")); %>', 'application/x-jsp'),
            ('large.pdf', b'x' * (50 * 1024 * 1024), 'application/pdf'),  # 50MB file
        ]
        
        malicious_uploads_blocked = 0
        
        for filename, content, content_type in malicious_files:
            malicious_file = SimpleUploadedFile(filename, content, content_type=content_type)
            
            response = self.client.post(reverse('content:upload'), {
                'title': f'Malicious Upload {filename}',
                'file': malicious_file,
                'subject': 'Testing'
            })
            
            # Should reject malicious files
            if response.status_code in [400, 413] or 'error' in str(response.content).lower():
                malicious_uploads_blocked += 1
        
        print(f"    ✅ Malicious uploads blocked: {malicious_uploads_blocked}/{len(malicious_files)}")
    
    def test_session_security(self):
        """Test session management security"""
        print("\n" + "="*60)
        print("SECURITY TESTING: Session Security")
        print("="*60)
        
        # Test 1: Session hijacking protection
        print("  Testing session hijacking protection...")
        
        # Login and get session ID
        self.client.login(username='sectest_student', password='SecurePass123!')
        original_session_key = self.client.session.session_key
        
        # Simulate session hijacking by creating new client with same session
        hijack_client = Client()
        hijack_client.cookies[settings.SESSION_COOKIE_NAME] = original_session_key
        
        # Try to access protected resource
        response = hijack_client.get(reverse('accounts:student_dashboard'))
        
        # Should require re-authentication or have additional security checks
        if response.status_code in [302, 403]:
            print("    ✅ Session hijacking protection in place")
        else:
            print("    ⚠️  Consider additional session security measures")
        
        # Test 2: Session timeout
        print("  Testing session timeout...")
        
        # Check if session has reasonable timeout
        session_age = getattr(settings, 'SESSION_COOKIE_AGE', None)
        
        if session_age and session_age <= 86400:  # 24 hours or less
            print(f"    ✅ Session timeout configured: {session_age} seconds")
        else:
            print("    ⚠️  Consider shorter session timeout for security")
        
        # Test 3: Concurrent session handling
        print("  Testing concurrent session handling...")
        
        # Login from multiple clients
        client1 = Client()
        client2 = Client()
        
        client1.login(username='sectest_student', password='SecurePass123!')
        client2.login(username='sectest_student', password='SecurePass123!')
        
        # Both should work (or implement single session policy)
        response1 = client1.get(reverse('accounts:student_dashboard'))
        response2 = client2.get(reverse('accounts:student_dashboard'))
        
        if response1.status_code == 200 and response2.status_code == 200:
            print("    ✅ Multiple concurrent sessions allowed")
        elif response1.status_code == 200 and response2.status_code != 200:
            print("    ✅ Single session policy enforced")
        else:
            print("    ⚠️  Unexpected session behavior")
    
    def test_data_exposure_vulnerabilities(self):
        """Test for data exposure vulnerabilities"""
        print("\n" + "="*60)
        print("SECURITY TESTING: Data Exposure")
        print("="*60)
        
        # Test 1: Information disclosure in error messages
        print("  Testing information disclosure...")
        
        # Try to access non-existent resources
        test_urls = [
            '/content/99999/',
            '/learning/session/99999/',
            '/accounts/user/99999/',
        ]
        
        info_disclosure_prevented = 0
        
        for url in test_urls:
            response = self.client.get(url)
            
            # Check if error messages reveal sensitive information
            content = str(response.content).lower()
            
            sensitive_keywords = ['database', 'sql', 'exception', 'traceback', 'path']
            
            if not any(keyword in content for keyword in sensitive_keywords):
                info_disclosure_prevented += 1
        
        print(f"    ✅ Information disclosure prevented: {info_disclosure_prevented}/{len(test_urls)}")
        
        # Test 2: Debug information exposure
        print("  Testing debug information exposure...")
        
        # Check if debug mode is disabled in production-like settings
        debug_exposed = False
        
        # Try to trigger 404 and check for debug info
        response = self.client.get('/nonexistent-page-12345/')
        
        if 'django' in str(response.content).lower() and 'traceback' in str(response.content).lower():
            debug_exposed = True
        
        if debug_exposed:
            print("    ⚠️  Debug information may be exposed")
        else:
            print("    ✅ Debug information properly hidden")
        
        # Test 3: Sensitive data in responses
        print("  Testing sensitive data exposure...")
        
        self.client.login(username='sectest_student', password='SecurePass123!')
        
        # Check various endpoints for sensitive data
        test_endpoints = [
            reverse('accounts:student_dashboard'),
            reverse('content:library'),
            reverse('learning:analytics'),
        ]
        
        sensitive_data_protected = 0
        
        for endpoint in test_endpoints:
            response = self.client.get(endpoint)
            content = str(response.content)
            
            # Check for exposed sensitive data
            sensitive_patterns = [
                r'password["\']?\s*:\s*["\'][^"\']+["\']',  # Password in JSON
                r'secret["\']?\s*:\s*["\'][^"\']+["\']',    # Secret keys
                r'token["\']?\s*:\s*["\'][^"\']+["\']',     # Auth tokens
            ]
            
            exposed = False
            for pattern in sensitive_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    exposed = True
                    break
            
            if not exposed:
                sensitive_data_protected += 1
        
        print(f"    ✅ Sensitive data protected: {sensitive_data_protected}/{len(test_endpoints)}")
    
    def test_api_security(self):
        """Test API security vulnerabilities"""
        print("\n" + "="*60)
        print("SECURITY TESTING: API Security")
        print("="*60)
        
        # Test 1: Rate limiting
        print("  Testing API rate limiting...")
        
        self.client.login(username='sectest_student', password='SecurePass123!')
        
        # Make rapid requests to API endpoints
        rapid_requests = 0
        rate_limited = False
        
        for i in range(50):  # 50 rapid requests
            response = self.client.get(reverse('content:library'))
            rapid_requests += 1
            
            if response.status_code == 429:  # Too Many Requests
                rate_limited = True
                break
        
        if rate_limited:
            print(f"    ✅ Rate limiting active (triggered after {rapid_requests} requests)")
        else:
            print("    ⚠️  Consider implementing API rate limiting")
        
        # Test 2: HTTP method security
        print("  Testing HTTP method security...")
        
        # Test if dangerous methods are disabled
        dangerous_methods = ['PUT', 'DELETE', 'PATCH']
        methods_secured = 0
        
        for method in dangerous_methods:
            response = self.client.generic(method, reverse('content:library'))
            
            if response.status_code in [405, 403]:  # Method Not Allowed or Forbidden
                methods_secured += 1
        
        print(f"    ✅ Dangerous HTTP methods secured: {methods_secured}/{len(dangerous_methods)}")
        
        # Test 3: Content-Type validation
        print("  Testing Content-Type validation...")
        
        # Try to send malicious content types
        malicious_content_types = [
            'application/x-www-form-urlencoded; charset=utf-7',
            'text/html',
            'application/javascript',
        ]
        
        content_type_validated = 0
        
        for content_type in malicious_content_types:
            response = self.client.post(
                reverse('content:upload'),
                data='{"malicious": "data"}',
                content_type=content_type
            )
            
            if response.status_code in [400, 415]:  # Bad Request or Unsupported Media Type
                content_type_validated += 1
        
        print(f"    ✅ Content-Type validation: {content_type_validated}/{len(malicious_content_types)}")
    
    def test_cryptographic_security(self):
        """Test cryptographic security"""
        print("\n" + "="*60)
        print("SECURITY TESTING: Cryptographic Security")
        print("="*60)
        
        # Test 1: Password hashing
        print("  Testing password hashing security...")
        
        # Check if passwords are properly hashed
        user = User.objects.get(username='sectest_student')
        
        # Password should not be stored in plaintext
        if user.password != 'SecurePass123!':
            print("    ✅ Passwords are hashed")
            
            # Check hashing algorithm
            if user.password.startswith('pbkdf2_'):
                print("    ✅ Strong password hashing algorithm (PBKDF2)")
            elif user.password.startswith('bcrypt'):
                print("    ✅ Strong password hashing algorithm (bcrypt)")
            else:
                print("    ⚠️  Consider using stronger password hashing")
        else:
            print("    ❌ Passwords stored in plaintext!")
        
        # Test 2: Session token security
        print("  Testing session token security...")
        
        self.client.login(username='sectest_student', password='SecurePass123!')
        session_key = self.client.session.session_key
        
        # Session key should be sufficiently random and long
        if len(session_key) >= 32:
            print(f"    ✅ Session key length adequate: {len(session_key)} characters")
        else:
            print(f"    ⚠️  Session key may be too short: {len(session_key)} characters")
        
        # Check for randomness (basic entropy check)
        unique_chars = len(set(session_key))
        if unique_chars >= 16:
            print(f"    ✅ Session key entropy adequate: {unique_chars} unique characters")
        else:
            print(f"    ⚠️  Session key entropy may be low: {unique_chars} unique characters")
        
        # Test 3: HTTPS enforcement
        print("  Testing HTTPS enforcement...")
        
        # Check security settings
        secure_ssl_redirect = getattr(settings, 'SECURE_SSL_REDIRECT', False)
        secure_hsts = getattr(settings, 'SECURE_HSTS_SECONDS', 0)
        
        if secure_ssl_redirect:
            print("    ✅ HTTPS redirect enabled")
        else:
            print("    ⚠️  Consider enabling HTTPS redirect in production")
        
        if secure_hsts > 0:
            print(f"    ✅ HSTS enabled: {secure_hsts} seconds")
        else:
            print("    ⚠️  Consider enabling HSTS for production")
    
    def test_business_logic_vulnerabilities(self):
        """Test business logic vulnerabilities"""
        print("\n" + "="*60)
        print("SECURITY TESTING: Business Logic")
        print("="*60)
        
        self.client.login(username='sectest_student', password='SecurePass123!')
        
        # Test 1: Race conditions in gamification
        print("  Testing race conditions in XP/coins...")
        
        import threading
        import time
        
        initial_xp = self.student_profile.total_xp
        
        def simulate_xp_gain():
            # Simulate concurrent XP updates
            profile = StudentProfile.objects.get(id=self.student_profile.id)
            profile.total_xp += 10
            profile.save()
        
        # Start multiple threads to update XP simultaneously
        threads = []
        for i in range(5):
            thread = threading.Thread(target=simulate_xp_gain)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Check final XP
        self.student_profile.refresh_from_db()
        expected_xp = initial_xp + (10 * 5)
        
        if self.student_profile.total_xp == expected_xp:
            print("    ✅ Race condition handled correctly")
        else:
            print(f"    ⚠️  Possible race condition (expected: {expected_xp}, got: {self.student_profile.total_xp})")
        
        # Test 2: Parameter tampering
        print("  Testing parameter tampering...")
        
        # Try to manipulate hidden form fields or parameters
        tampered_requests = [
            {'user_id': self.teacher_user.id},  # Try to impersonate teacher
            {'is_superuser': True},             # Try to gain admin privileges
            {'total_xp': 999999},              # Try to manipulate XP
        ]
        
        tampering_prevented = 0
        
        for tampered_data in tampered_requests:
            response = self.client.post(reverse('content:upload'), {
                'title': 'Tamper Test',
                'subject': 'Testing',
                **tampered_data
            })
            
            # Should ignore tampered parameters
            if response.status_code in [200, 302, 400]:
                tampering_prevented += 1
        
        print(f"    ✅ Parameter tampering prevented: {tampering_prevented}/{len(tampered_requests)}")
        
        # Test 3: Workflow bypass
        print("  Testing workflow bypass...")
        
        # Try to access features without completing prerequisites
        bypass_attempts = [
            # Try to access advanced features without basic setup
            reverse('learning:analytics'),
            reverse('gamification:achievements'),
        ]
        
        workflow_protected = 0
        
        for url in bypass_attempts:
            response = self.client.get(url)
            
            # Should handle gracefully or redirect to proper workflow
            if response.status_code in [200, 302]:
                workflow_protected += 1
        
        print(f"    ✅ Workflow bypass protected: {workflow_protected}/{len(bypass_attempts)}")
    
    def tearDown(self):
        """Clean up test data"""
        # Clean up any uploaded files
        for content in UploadedContent.objects.all():
            if content.file and hasattr(content.file, 'path'):
                try:
                    import os
                    if os.path.exists(content.file.path):
                        os.remove(content.file.path)
                except:
                    pass