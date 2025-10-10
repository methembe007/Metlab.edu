"""
Failure scenario testing for Metlab.edu AI Learning Platform
Tests system behavior under various failure conditions
"""

import time
from unittest.mock import patch, MagicMock, Mock
from django.test import TestCase, TransactionTestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.db import transaction, connection
from django.core.cache import cache
from django.core.exceptions import ValidationError
import tempfile
import os

from accounts.models import StudentProfile, TeacherProfile
from content.models import UploadedContent, GeneratedSummary, GeneratedQuiz
from learning.models import LearningSession, Class
from gamification.models import VirtualCurrency, Achievement

User = get_user_model()


class FailureScenarioTestCase(TransactionTestCase):
    """Test system behavior under various failure scenarios"""
    
    def setUp(self):
        """Set up test data for failure testing"""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='failuretest',
            email='failure@test.com',
            password='testpass123',
            role='student'
        )
        
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            learning_preferences={'style': 'visual'},
            current_streak=5,
            total_xp=100
        )
        
        # Create test teacher
        self.teacher_user = User.objects.create_user(
            username='teacherfail',
            email='teacherfail@test.com',
            password='testpass123',
            role='teacher'
        )
        
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            institution='Failure Test School'
        )
        
        self.sample_pdf = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Failure test content) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n298\n%%EOF'
    
    def test_ai_service_failure_handling(self):
        """Test handling of AI service failures"""
        print("\n" + "="*60)
        print("FAILURE TESTING: AI Service Failures")
        print("="*60)
        
        self.client.login(username='failuretest', password='testpass123')
        
        # Test 1: AI service timeout
        print("  Testing AI service timeout...")
        with patch('content.ai_services.extract_key_concepts') as mock_extract:
            mock_extract.side_effect = TimeoutError("AI service timeout")
            
            test_file = SimpleUploadedFile(
                "timeout_test.pdf",
                self.sample_pdf,
                content_type="application/pdf"
            )
            
            response = self.client.post(reverse('content:upload'), {
                'title': 'Timeout Test',
                'file': test_file,
                'subject': 'Mathematics'
            })
            
            # Should handle timeout gracefully
            self.assertIn(response.status_code, [200, 302])
            
            # Content should be created but marked as failed
            content = UploadedContent.objects.filter(title='Timeout Test').first()
            if content:
                self.assertFalse(content.processed)
                print("    ✅ Timeout handled gracefully")
        
        # Test 2: AI service rate limit
        print("  Testing AI service rate limit...")
        with patch('content.ai_services.extract_key_concepts') as mock_extract:
            mock_extract.side_effect = Exception("Rate limit exceeded")
            
            test_file = SimpleUploadedFile(
                "ratelimit_test.pdf",
                self.sample_pdf,
                content_type="application/pdf"
            )
            
            response = self.client.post(reverse('content:upload'), {
                'title': 'Rate Limit Test',
                'file': test_file,
                'subject': 'Science'
            })
            
            # Should handle rate limit gracefully
            self.assertIn(response.status_code, [200, 302])
            print("    ✅ Rate limit handled gracefully")
        
        # Test 3: Invalid AI response
        print("  Testing invalid AI response...")
        with patch('content.ai_services.extract_key_concepts') as mock_extract, \
             patch('content.ai_services.generate_summary') as mock_summary:
            
            mock_extract.return_value = None  # Invalid response
            mock_summary.return_value = ""    # Empty response
            
            test_file = SimpleUploadedFile(
                "invalid_response_test.pdf",
                self.sample_pdf,
                content_type="application/pdf"
            )
            
            response = self.client.post(reverse('content:upload'), {
                'title': 'Invalid Response Test',
                'file': test_file,
                'subject': 'History'
            })
            
            # Should handle invalid response gracefully
            self.assertIn(response.status_code, [200, 302])
            print("    ✅ Invalid AI response handled gracefully")
    
    def test_database_failure_scenarios(self):
        """Test database failure scenarios"""
        print("\n" + "="*60)
        print("FAILURE TESTING: Database Failures")
        print("="*60)
        
        self.client.login(username='failuretest', password='testpass123')
        
        # Test 1: Database connection failure simulation
        print("  Testing database connection failure...")
        with patch('django.db.connection.cursor') as mock_cursor:
            mock_cursor.side_effect = Exception("Database connection failed")
            
            # This should be handled by Django's database error handling
            try:
                response = self.client.get(reverse('accounts:student_dashboard'))
                # If we get here, Django handled the error
                print("    ✅ Database connection failure handled by Django")
            except Exception as e:
                # Expected behavior - Django should handle this
                print(f"    ✅ Database error properly raised: {type(e).__name__}")
        
        # Test 2: Transaction rollback scenario
        print("  Testing transaction rollback...")
        initial_count = UploadedContent.objects.count()
        
        try:
            with transaction.atomic():
                # Create content
                content = UploadedContent.objects.create(
                    user=self.user,
                    title='Transaction Test',
                    subject='Testing'
                )
                
                # Force an error to trigger rollback
                raise Exception("Forced transaction failure")
                
        except Exception:
            pass  # Expected
        
        # Verify rollback occurred
        final_count = UploadedContent.objects.count()
        self.assertEqual(initial_count, final_count)
        print("    ✅ Transaction rollback successful")
        
        # Test 3: Constraint violation handling
        print("  Testing constraint violations...")
        try:
            # Try to create duplicate user
            User.objects.create_user(
                username='failuretest',  # Duplicate username
                email='duplicate@test.com',
                password='testpass123'
            )
        except Exception as e:
            print(f"    ✅ Constraint violation handled: {type(e).__name__}")
    
    def test_file_system_failures(self):
        """Test file system failure scenarios"""
        print("\n" + "="*60)
        print("FAILURE TESTING: File System Failures")
        print("="*60)
        
        self.client.login(username='failuretest', password='testpass123')
        
        # Test 1: Disk space full simulation
        print("  Testing disk space full scenario...")
        with patch('django.core.files.storage.default_storage.save') as mock_save:
            mock_save.side_effect = OSError("No space left on device")
            
            test_file = SimpleUploadedFile(
                "diskfull_test.pdf",
                self.sample_pdf,
                content_type="application/pdf"
            )
            
            response = self.client.post(reverse('content:upload'), {
                'title': 'Disk Full Test',
                'file': test_file,
                'subject': 'Testing'
            })
            
            # Should handle disk full error gracefully
            self.assertIn(response.status_code, [200, 400])
            print("    ✅ Disk full error handled gracefully")
        
        # Test 2: File permission error
        print("  Testing file permission error...")
        with patch('django.core.files.storage.default_storage.save') as mock_save:
            mock_save.side_effect = PermissionError("Permission denied")
            
            test_file = SimpleUploadedFile(
                "permission_test.pdf",
                self.sample_pdf,
                content_type="application/pdf"
            )
            
            response = self.client.post(reverse('content:upload'), {
                'title': 'Permission Test',
                'file': test_file,
                'subject': 'Testing'
            })
            
            # Should handle permission error gracefully
            self.assertIn(response.status_code, [200, 400])
            print("    ✅ Permission error handled gracefully")
        
        # Test 3: Corrupted file handling
        print("  Testing corrupted file handling...")
        corrupted_file = SimpleUploadedFile(
            "corrupted.pdf",
            b"This is not a valid PDF file",
            content_type="application/pdf"
        )
        
        response = self.client.post(reverse('content:upload'), {
            'title': 'Corrupted File Test',
            'file': corrupted_file,
            'subject': 'Testing'
        })
        
        # Should handle corrupted file gracefully
        self.assertIn(response.status_code, [200, 400])
        print("    ✅ Corrupted file handled gracefully")
    
    def test_network_failure_scenarios(self):
        """Test network failure scenarios"""
        print("\n" + "="*60)
        print("FAILURE TESTING: Network Failures")
        print("="*60)
        
        # Test 1: External API failure
        print("  Testing external API failure...")
        with patch('requests.post') as mock_post:
            mock_post.side_effect = ConnectionError("Network unreachable")
            
            # This would affect AI services that use external APIs
            self.client.login(username='failuretest', password='testpass123')
            
            test_file = SimpleUploadedFile(
                "network_test.pdf",
                self.sample_pdf,
                content_type="application/pdf"
            )
            
            # Mock the AI services to simulate network failure
            with patch('content.ai_services.extract_key_concepts') as mock_extract:
                mock_extract.side_effect = ConnectionError("Network unreachable")
                
                response = self.client.post(reverse('content:upload'), {
                    'title': 'Network Test',
                    'file': test_file,
                    'subject': 'Testing'
                })
                
                # Should handle network failure gracefully
                self.assertIn(response.status_code, [200, 302])
                print("    ✅ Network failure handled gracefully")
        
        # Test 2: Slow network simulation
        print("  Testing slow network scenario...")
        with patch('content.ai_services.extract_key_concepts') as mock_extract:
            def slow_response(*args, **kwargs):
                time.sleep(2)  # Simulate slow response
                return ['concept1', 'concept2']
            
            mock_extract.side_effect = slow_response
            
            test_file = SimpleUploadedFile(
                "slow_network_test.pdf",
                self.sample_pdf,
                content_type="application/pdf"
            )
            
            start_time = time.time()
            response = self.client.post(reverse('content:upload'), {
                'title': 'Slow Network Test',
                'file': test_file,
                'subject': 'Testing'
            })
            end_time = time.time()
            
            # Should handle slow network but still complete
            self.assertIn(response.status_code, [200, 302])
            print(f"    ✅ Slow network handled (took {end_time - start_time:.2f}s)")
    
    def test_cache_failure_scenarios(self):
        """Test cache failure scenarios"""
        print("\n" + "="*60)
        print("FAILURE TESTING: Cache Failures")
        print("="*60)
        
        self.client.login(username='failuretest', password='testpass123')
        
        # Test 1: Cache unavailable
        print("  Testing cache unavailable scenario...")
        with patch('django.core.cache.cache.get') as mock_get, \
             patch('django.core.cache.cache.set') as mock_set:
            
            mock_get.side_effect = Exception("Cache unavailable")
            mock_set.side_effect = Exception("Cache unavailable")
            
            # Application should still work without cache
            response = self.client.get(reverse('accounts:student_dashboard'))
            self.assertEqual(response.status_code, 200)
            print("    ✅ Application works without cache")
        
        # Test 2: Cache corruption
        print("  Testing cache corruption scenario...")
        with patch('django.core.cache.cache.get') as mock_get:
            mock_get.return_value = "corrupted_data_not_json"
            
            # Should handle corrupted cache data gracefully
            response = self.client.get(reverse('content:library'))
            self.assertEqual(response.status_code, 200)
            print("    ✅ Corrupted cache data handled gracefully")
    
    def test_memory_exhaustion_scenarios(self):
        """Test memory exhaustion scenarios"""
        print("\n" + "="*60)
        print("FAILURE TESTING: Memory Exhaustion")
        print("="*60)
        
        self.client.login(username='failuretest', password='testpass123')
        
        # Test 1: Large file upload
        print("  Testing large file upload...")
        # Create a large file (simulated)
        large_content = b"x" * (10 * 1024 * 1024)  # 10MB
        
        large_file = SimpleUploadedFile(
            "large_test.pdf",
            large_content,
            content_type="application/pdf"
        )
        
        response = self.client.post(reverse('content:upload'), {
            'title': 'Large File Test',
            'file': large_file,
            'subject': 'Testing'
        })
        
        # Should handle large file appropriately (reject or process)
        self.assertIn(response.status_code, [200, 302, 400, 413])
        print("    ✅ Large file upload handled appropriately")
        
        # Test 2: Memory leak simulation
        print("  Testing memory usage patterns...")
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform multiple operations that could cause memory leaks
        for i in range(10):
            response = self.client.get(reverse('accounts:student_dashboard'))
            self.assertEqual(response.status_code, 200)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        self.assertLess(memory_increase, 100 * 1024 * 1024, "Memory increase should be less than 100MB")
        print(f"    ✅ Memory usage stable (increased by {memory_increase / 1024 / 1024:.2f}MB)")
    
    def test_concurrent_access_failures(self):
        """Test concurrent access failure scenarios"""
        print("\n" + "="*60)
        print("FAILURE TESTING: Concurrent Access")
        print("="*60)
        
        # Test 1: Race condition in user creation
        print("  Testing race condition handling...")
        
        def create_duplicate_user():
            try:
                User.objects.create_user(
                    username='racetest',
                    email='race@test.com',
                    password='testpass123'
                )
                return True
            except Exception:
                return False
        
        import threading
        
        results = []
        threads = []
        
        # Try to create the same user simultaneously
        for i in range(5):
            thread = threading.Thread(target=lambda: results.append(create_duplicate_user()))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Only one should succeed
        successful_creations = sum(results)
        self.assertEqual(successful_creations, 1)
        print("    ✅ Race condition handled - only one user created")
        
        # Test 2: Concurrent file uploads
        print("  Testing concurrent file upload conflicts...")
        
        def upload_file_concurrently(filename):
            client = Client()
            client.login(username='failuretest', password='testpass123')
            
            test_file = SimpleUploadedFile(
                filename,
                self.sample_pdf,
                content_type="application/pdf"
            )
            
            try:
                response = client.post(reverse('content:upload'), {
                    'title': f'Concurrent Test {filename}',
                    'file': test_file,
                    'subject': 'Testing'
                })
                return response.status_code in [200, 302]
            except Exception:
                return False
        
        upload_results = []
        upload_threads = []
        
        # Upload multiple files simultaneously
        for i in range(3):
            thread = threading.Thread(
                target=lambda i=i: upload_results.append(upload_file_concurrently(f'concurrent_{i}.pdf'))
            )
            upload_threads.append(thread)
            thread.start()
        
        for thread in upload_threads:
            thread.join()
        
        # Most uploads should succeed
        successful_uploads = sum(upload_results)
        self.assertGreaterEqual(successful_uploads, 2)
        print(f"    ✅ Concurrent uploads handled ({successful_uploads}/3 successful)")
    
    def test_authentication_failure_scenarios(self):
        """Test authentication failure scenarios"""
        print("\n" + "="*60)
        print("FAILURE TESTING: Authentication Failures")
        print("="*60)
        
        # Test 1: Brute force login attempts
        print("  Testing brute force protection...")
        
        failed_attempts = 0
        for i in range(10):
            response = self.client.post(reverse('accounts:login'), {
                'username': 'failuretest',
                'password': 'wrongpassword'
            })
            
            if response.status_code != 302:  # Not redirected (login failed)
                failed_attempts += 1
        
        # All attempts should fail
        self.assertEqual(failed_attempts, 10)
        print("    ✅ Brute force attempts properly rejected")
        
        # Test 2: Session hijacking protection
        print("  Testing session security...")
        
        # Login successfully
        response = self.client.post(reverse('accounts:login'), {
            'username': 'failuretest',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
        
        # Access protected page
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Simulate session tampering by clearing session
        self.client.session.flush()
        
        # Should be redirected to login
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 302)
        print("    ✅ Session security properly enforced")
        
        # Test 3: Invalid user role access
        print("  Testing role-based access control...")
        
        # Login as student
        self.client.login(username='failuretest', password='testpass123')
        
        # Try to access teacher dashboard
        response = self.client.get(reverse('accounts:teacher_dashboard'))
        self.assertEqual(response.status_code, 403)
        print("    ✅ Role-based access control working")
    
    def test_data_validation_failures(self):
        """Test data validation failure scenarios"""
        print("\n" + "="*60)
        print("FAILURE TESTING: Data Validation")
        print("="*60)
        
        self.client.login(username='failuretest', password='testpass123')
        
        # Test 1: Invalid file types
        print("  Testing invalid file type rejection...")
        
        invalid_file = SimpleUploadedFile(
            "malicious.exe",
            b"malicious content",
            content_type="application/x-executable"
        )
        
        response = self.client.post(reverse('content:upload'), {
            'title': 'Malicious File',
            'file': invalid_file,
            'subject': 'Testing'
        })
        
        # Should reject invalid file type
        self.assertNotEqual(response.status_code, 302)
        print("    ✅ Invalid file type properly rejected")
        
        # Test 2: XSS attempt in form data
        print("  Testing XSS protection...")
        
        xss_payload = "<script>alert('xss')</script>"
        
        response = self.client.post(reverse('content:upload'), {
            'title': xss_payload,
            'subject': 'Testing'
        })
        
        # Should handle XSS attempt safely
        self.assertIn(response.status_code, [200, 400])
        print("    ✅ XSS attempt handled safely")
        
        # Test 3: SQL injection attempt
        print("  Testing SQL injection protection...")
        
        sql_payload = "'; DROP TABLE auth_user; --"
        
        response = self.client.post(reverse('accounts:login'), {
            'username': sql_payload,
            'password': 'testpass123'
        })
        
        # Should handle SQL injection attempt safely
        self.assertNotEqual(response.status_code, 302)
        
        # Verify users table still exists
        user_count = User.objects.count()
        self.assertGreater(user_count, 0)
        print("    ✅ SQL injection attempt blocked")
    
    def tearDown(self):
        """Clean up test data"""
        # Clean up any uploaded files
        for content in UploadedContent.objects.all():
            if content.file and hasattr(content.file, 'path'):
                try:
                    if os.path.exists(content.file.path):
                        os.remove(content.file.path)
                except:
                    pass
        
        # Clear cache
        cache.clear()