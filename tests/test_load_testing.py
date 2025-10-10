"""
Load testing for Metlab.edu AI Learning Platform
Tests system performance under concurrent user load
"""

import threading
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.test import TestCase, TransactionTestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.db import transaction
from unittest.mock import patch
import statistics

from accounts.models import StudentProfile, TeacherProfile, ParentProfile
from content.models import UploadedContent
from learning.models import LearningSession
from gamification.models import VirtualCurrency

User = get_user_model()


class LoadTestingCase(TransactionTestCase):
    """Load testing with multiple concurrent users"""
    
    def setUp(self):
        """Set up test data for load testing"""
        self.test_users = []
        self.test_content = []
        
        # Create test users for different roles
        for i in range(50):  # 50 test users
            user = User.objects.create_user(
                username=f'loadtest_user_{i}',
                email=f'loadtest{i}@test.com',
                password='testpass123',
                role='student'
            )
            
            profile = StudentProfile.objects.create(
                user=user,
                learning_preferences={'style': 'visual', 'pace': 'medium'},
                current_streak=random.randint(0, 10),
                total_xp=random.randint(0, 1000)
            )
            
            self.test_users.append((user, profile))
        
        # Create test teachers
        for i in range(10):  # 10 test teachers
            teacher_user = User.objects.create_user(
                username=f'teacher_{i}',
                email=f'teacher{i}@test.com',
                password='testpass123',
                role='teacher'
            )
            
            TeacherProfile.objects.create(
                user=teacher_user,
                institution='Load Test School'
            )
        
        # Create sample content
        self.sample_pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Load test content) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n298\n%%EOF'
    
    def simulate_user_session(self, user_data, session_duration=30):
        """Simulate a complete user session"""
        user, profile = user_data
        client = Client()
        
        session_stats = {
            'user_id': user.id,
            'login_time': 0,
            'dashboard_time': 0,
            'upload_time': 0,
            'learning_time': 0,
            'total_requests': 0,
            'errors': 0,
            'start_time': time.time()
        }
        
        try:
            # 1. Login
            start_time = time.time()
            login_response = client.post(reverse('accounts:login'), {
                'username': user.username,
                'password': 'testpass123'
            })
            session_stats['login_time'] = time.time() - start_time
            session_stats['total_requests'] += 1
            
            if login_response.status_code != 302:
                session_stats['errors'] += 1
                return session_stats
            
            # 2. Access dashboard
            start_time = time.time()
            dashboard_response = client.get(reverse('accounts:student_dashboard'))
            session_stats['dashboard_time'] = time.time() - start_time
            session_stats['total_requests'] += 1
            
            if dashboard_response.status_code != 200:
                session_stats['errors'] += 1
            
            # 3. Upload content (with mocked AI processing)
            with patch('content.ai_services.extract_key_concepts') as mock_extract, \
                 patch('content.ai_services.generate_summary') as mock_summary, \
                 patch('content.ai_services.generate_quiz') as mock_quiz, \
                 patch('content.ai_services.generate_flashcards') as mock_flashcards:
                
                mock_extract.return_value = ['concept1', 'concept2']
                mock_summary.return_value = 'Test summary'
                mock_quiz.return_value = {'questions': []}
                mock_flashcards.return_value = []
                
                start_time = time.time()
                test_file = SimpleUploadedFile(
                    f"loadtest_{user.id}.pdf",
                    self.sample_pdf_content,
                    content_type="application/pdf"
                )
                
                upload_response = client.post(reverse('content:upload'), {
                    'title': f'Load Test Document {user.id}',
                    'file': test_file,
                    'subject': 'Mathematics'
                })
                session_stats['upload_time'] = time.time() - start_time
                session_stats['total_requests'] += 1
                
                if upload_response.status_code not in [200, 302]:
                    session_stats['errors'] += 1
            
            # 4. Browse content library
            library_response = client.get(reverse('content:library'))
            session_stats['total_requests'] += 1
            
            if library_response.status_code != 200:
                session_stats['errors'] += 1
            
            # 5. Start learning session
            if UploadedContent.objects.filter(user=user).exists():
                content = UploadedContent.objects.filter(user=user).first()
                
                start_time = time.time()
                session_response = client.post(reverse('learning:start_session'), {
                    'content_id': content.id
                })
                session_stats['learning_time'] = time.time() - start_time
                session_stats['total_requests'] += 1
                
                if session_response.status_code not in [200, 302]:
                    session_stats['errors'] += 1
            
            # 6. Check gamification features
            achievements_response = client.get(reverse('gamification:achievements'))
            session_stats['total_requests'] += 1
            
            if achievements_response.status_code != 200:
                session_stats['errors'] += 1
            
            # 7. View analytics
            analytics_response = client.get(reverse('learning:analytics'))
            session_stats['total_requests'] += 1
            
            if analytics_response.status_code != 200:
                session_stats['errors'] += 1
            
        except Exception as e:
            session_stats['errors'] += 1
            session_stats['exception'] = str(e)
        
        session_stats['total_time'] = time.time() - session_stats['start_time']
        return session_stats
    
    def test_concurrent_user_load(self):
        """Test system with multiple concurrent users"""
        print("\n" + "="*60)
        print("LOAD TESTING: Concurrent User Sessions")
        print("="*60)
        
        # Test with different concurrency levels
        concurrency_levels = [5, 10, 20, 30]
        
        for concurrent_users in concurrency_levels:
            print(f"\nTesting with {concurrent_users} concurrent users...")
            
            # Select random users for this test
            test_users = random.sample(self.test_users, concurrent_users)
            
            start_time = time.time()
            
            # Run concurrent sessions
            with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
                futures = [
                    executor.submit(self.simulate_user_session, user_data)
                    for user_data in test_users
                ]
                
                results = []
                for future in as_completed(futures):
                    try:
                        result = future.result(timeout=60)  # 60 second timeout
                        results.append(result)
                    except Exception as e:
                        results.append({
                            'errors': 1,
                            'exception': str(e),
                            'total_time': 60
                        })
            
            total_time = time.time() - start_time
            
            # Analyze results
            successful_sessions = [r for r in results if r.get('errors', 0) == 0]
            failed_sessions = [r for r in results if r.get('errors', 0) > 0]
            
            if successful_sessions:
                avg_session_time = statistics.mean([r['total_time'] for r in successful_sessions])
                avg_login_time = statistics.mean([r.get('login_time', 0) for r in successful_sessions])
                avg_dashboard_time = statistics.mean([r.get('dashboard_time', 0) for r in successful_sessions])
                avg_upload_time = statistics.mean([r.get('upload_time', 0) for r in successful_sessions])
                
                total_requests = sum([r.get('total_requests', 0) for r in results])
                requests_per_second = total_requests / total_time if total_time > 0 else 0
                
                print(f"  ✅ Successful sessions: {len(successful_sessions)}/{concurrent_users}")
                print(f"  ⏱️  Average session time: {avg_session_time:.2f}s")
                print(f"  🔐 Average login time: {avg_login_time:.2f}s")
                print(f"  📊 Average dashboard load: {avg_dashboard_time:.2f}s")
                print(f"  📤 Average upload time: {avg_upload_time:.2f}s")
                print(f"  🚀 Requests per second: {requests_per_second:.2f}")
                
                # Performance assertions
                self.assertLess(avg_login_time, 5.0, "Login should complete within 5 seconds")
                self.assertLess(avg_dashboard_time, 3.0, "Dashboard should load within 3 seconds")
                self.assertLess(avg_upload_time, 10.0, "Upload should complete within 10 seconds")
                
            else:
                print(f"  ❌ All sessions failed")
            
            if failed_sessions:
                print(f"  ⚠️  Failed sessions: {len(failed_sessions)}")
                for i, session in enumerate(failed_sessions[:3]):  # Show first 3 failures
                    print(f"    - Session {i+1}: {session.get('exception', 'Unknown error')}")
            
            # Assert success rate
            success_rate = len(successful_sessions) / concurrent_users
            self.assertGreaterEqual(success_rate, 0.8, f"Success rate should be at least 80% for {concurrent_users} users")
    
    def test_database_performance_under_load(self):
        """Test database performance with concurrent operations"""
        print("\n" + "="*60)
        print("LOAD TESTING: Database Performance")
        print("="*60)
        
        def create_learning_session(user_data):
            """Create learning session for load testing"""
            user, profile = user_data
            
            try:
                with transaction.atomic():
                    # Create content
                    content = UploadedContent.objects.create(
                        user=user,
                        title=f'DB Load Test {user.id}',
                        subject='Testing',
                        processed=True
                    )
                    
                    # Create learning session
                    session = LearningSession.objects.create(
                        student=profile,
                        content=content,
                        performance_score=random.uniform(0.5, 1.0)
                    )
                    
                    # Update virtual currency
                    currency, created = VirtualCurrency.objects.get_or_create(
                        student=profile,
                        defaults={'coins': 0}
                    )
                    currency.coins += random.randint(1, 10)
                    currency.save()
                    
                    return True
            except Exception as e:
                print(f"Database operation failed: {e}")
                return False
        
        # Test with 20 concurrent database operations
        concurrent_ops = 20
        test_users = random.sample(self.test_users, concurrent_ops)
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_ops) as executor:
            futures = [
                executor.submit(create_learning_session, user_data)
                for user_data in test_users
            ]
            
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=30)
                    results.append(result)
                except Exception as e:
                    results.append(False)
        
        total_time = time.time() - start_time
        successful_ops = sum(results)
        
        print(f"  ✅ Successful operations: {successful_ops}/{concurrent_ops}")
        print(f"  ⏱️  Total time: {total_time:.2f}s")
        print(f"  🚀 Operations per second: {successful_ops/total_time:.2f}")
        
        # Assert performance
        self.assertGreaterEqual(successful_ops/concurrent_ops, 0.9, "Database operations should have 90% success rate")
        self.assertLess(total_time, 30, "All database operations should complete within 30 seconds")
    
    def test_memory_usage_under_load(self):
        """Test memory usage patterns under load"""
        print("\n" + "="*60)
        print("LOAD TESTING: Memory Usage")
        print("="*60)
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"  📊 Initial memory usage: {initial_memory:.2f} MB")
        
        # Simulate memory-intensive operations
        def memory_intensive_operation(user_data):
            """Simulate memory-intensive user operations"""
            user, profile = user_data
            client = Client()
            
            # Login
            client.post(reverse('accounts:login'), {
                'username': user.username,
                'password': 'testpass123'
            })
            
            # Multiple dashboard requests
            for _ in range(5):
                client.get(reverse('accounts:student_dashboard'))
            
            # Multiple content library requests
            for _ in range(3):
                client.get(reverse('content:library'))
            
            return True
        
        # Run 15 concurrent memory-intensive operations
        concurrent_ops = 15
        test_users = random.sample(self.test_users, concurrent_ops)
        
        with ThreadPoolExecutor(max_workers=concurrent_ops) as executor:
            futures = [
                executor.submit(memory_intensive_operation, user_data)
                for user_data in test_users
            ]
            
            for future in as_completed(futures):
                future.result()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"  📊 Final memory usage: {final_memory:.2f} MB")
        print(f"  📈 Memory increase: {memory_increase:.2f} MB")
        
        # Assert reasonable memory usage
        self.assertLess(memory_increase, 500, "Memory increase should be less than 500MB")
        self.assertLess(final_memory, 1000, "Total memory usage should be less than 1GB")
    
    def test_file_upload_concurrency(self):
        """Test concurrent file uploads"""
        print("\n" + "="*60)
        print("LOAD TESTING: Concurrent File Uploads")
        print("="*60)
        
        def upload_file(user_data):
            """Upload file for load testing"""
            user, profile = user_data
            client = Client()
            
            # Login
            login_response = client.post(reverse('accounts:login'), {
                'username': user.username,
                'password': 'testpass123'
            })
            
            if login_response.status_code != 302:
                return False
            
            # Mock AI processing to avoid external API calls
            with patch('content.ai_services.extract_key_concepts') as mock_extract, \
                 patch('content.ai_services.generate_summary') as mock_summary, \
                 patch('content.ai_services.generate_quiz') as mock_quiz, \
                 patch('content.ai_services.generate_flashcards') as mock_flashcards:
                
                mock_extract.return_value = ['test', 'concept']
                mock_summary.return_value = 'Test summary'
                mock_quiz.return_value = {'questions': []}
                mock_flashcards.return_value = []
                
                test_file = SimpleUploadedFile(
                    f"concurrent_test_{user.id}.pdf",
                    self.sample_pdf_content,
                    content_type="application/pdf"
                )
                
                upload_response = client.post(reverse('content:upload'), {
                    'title': f'Concurrent Upload Test {user.id}',
                    'file': test_file,
                    'subject': 'Testing'
                })
                
                return upload_response.status_code in [200, 302]
        
        # Test with 10 concurrent uploads
        concurrent_uploads = 10
        test_users = random.sample(self.test_users, concurrent_uploads)
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_uploads) as executor:
            futures = [
                executor.submit(upload_file, user_data)
                for user_data in test_users
            ]
            
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=60)
                    results.append(result)
                except Exception as e:
                    results.append(False)
        
        total_time = time.time() - start_time
        successful_uploads = sum(results)
        
        print(f"  ✅ Successful uploads: {successful_uploads}/{concurrent_uploads}")
        print(f"  ⏱️  Total time: {total_time:.2f}s")
        print(f"  📤 Uploads per second: {successful_uploads/total_time:.2f}")
        
        # Assert performance
        self.assertGreaterEqual(successful_uploads/concurrent_uploads, 0.8, "Upload success rate should be at least 80%")
        self.assertLess(total_time, 120, "All uploads should complete within 2 minutes")
    
    def tearDown(self):
        """Clean up test data"""
        # Clean up uploaded files
        for content in UploadedContent.objects.all():
            if content.file and hasattr(content.file, 'path'):
                try:
                    import os
                    if os.path.exists(content.file.path):
                        os.remove(content.file.path)
                except:
                    pass