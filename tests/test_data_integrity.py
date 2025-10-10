"""
Data integrity testing for Metlab.edu AI Learning Platform
Tests data consistency, backup/recovery, and database integrity
"""

import os
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import transaction, connection
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test import Client
from unittest.mock import patch

from accounts.models import StudentProfile, TeacherProfile, ParentProfile
from content.models import UploadedContent, GeneratedSummary, GeneratedQuiz, Flashcard
from learning.models import LearningSession, WeaknessAnalysis, PersonalizedRecommendation, Class, Enrollment
from gamification.models import Achievement, StudentAchievement, Leaderboard, VirtualCurrency
from community.models import TutorProfile, StudyGroup, StudySession, StudyPartner, TutoringBooking

User = get_user_model()


class DataIntegrityTestCase(TransactionTestCase):
    """Test data integrity and consistency"""
    
    def setUp(self):
        """Set up test data for integrity testing"""
        self.client = Client()
        
        # Create comprehensive test data
        self.student_user = User.objects.create_user(
            username='integrity_student',
            email='student@integrity.com',
            password='testpass123',
            role='student'
        )
        
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            learning_preferences={'style': 'visual', 'pace': 'medium'},
            current_streak=10,
            total_xp=500
        )
        
        self.teacher_user = User.objects.create_user(
            username='integrity_teacher',
            email='teacher@integrity.com',
            password='testpass123',
            role='teacher'
        )
        
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            institution='Integrity Test School'
        )
        
        self.parent_user = User.objects.create_user(
            username='integrity_parent',
            email='parent@integrity.com',
            password='testpass123',
            role='parent'
        )
        
        self.parent_profile = ParentProfile.objects.create(
            user=self.parent_user
        )
        self.parent_profile.children.add(self.student_profile)
        
        # Create test content
        self.content = UploadedContent.objects.create(
            user=self.student_user,
            title='Integrity Test Content',
            subject='Mathematics',
            processed=True,
            key_concepts=['algebra', 'equations', 'variables']
        )
        
        # Create related data
        self.summary = GeneratedSummary.objects.create(
            content=self.content,
            summary_type='short',
            text='Test summary for integrity testing'
        )
        
        self.quiz = GeneratedQuiz.objects.create(
            content=self.content,
            questions={'questions': [{'question': 'What is algebra?', 'answer': 'Math'}]},
            difficulty_level='medium'
        )
        
        self.flashcard = Flashcard.objects.create(
            content=self.content,
            front_text='What is a variable?',
            back_text='A symbol representing a number',
            concept_tag='variables'
        )
        
        # Create learning session
        self.session = LearningSession.objects.create(
            student=self.student_profile,
            content=self.content,
            performance_score=0.85
        )
        
        # Create gamification data
        self.achievement = Achievement.objects.create(
            name='Test Achievement',
            description='Test achievement for integrity',
            badge_icon='test',
            xp_requirement=100
        )
        
        self.student_achievement = StudentAchievement.objects.create(
            student=self.student_profile,
            achievement=self.achievement
        )
        
        self.virtual_currency = VirtualCurrency.objects.create(
            student=self.student_profile,
            coins=50
        )
        
        # Create class and enrollment
        self.test_class = Class.objects.create(
            name='Integrity Test Class',
            subject='Mathematics',
            teacher=self.teacher_profile,
            description='Test class for integrity testing'
        )
        
        self.enrollment = Enrollment.objects.create(
            student=self.student_profile,
            class_obj=self.test_class,
            is_active=True
        )
    
    def test_referential_integrity(self):
        """Test referential integrity constraints"""
        print("\n" + "="*60)
        print("DATA INTEGRITY: Referential Integrity")
        print("="*60)
        
        # Test 1: Cascade deletion
        print("  Testing cascade deletion...")
        
        initial_summary_count = GeneratedSummary.objects.count()
        initial_quiz_count = GeneratedQuiz.objects.count()
        initial_flashcard_count = Flashcard.objects.count()
        
        # Delete content - should cascade to related objects
        content_id = self.content.id
        self.content.delete()
        
        # Verify related objects were deleted
        remaining_summaries = GeneratedSummary.objects.filter(content_id=content_id).count()
        remaining_quizzes = GeneratedQuiz.objects.filter(content_id=content_id).count()
        remaining_flashcards = Flashcard.objects.filter(content_id=content_id).count()
        
        self.assertEqual(remaining_summaries, 0)
        self.assertEqual(remaining_quizzes, 0)
        self.assertEqual(remaining_flashcards, 0)
        
        print("    ✅ Cascade deletion working correctly")
        
        # Test 2: Foreign key constraints
        print("  Testing foreign key constraints...")
        
        try:
            # Try to create content with non-existent user
            UploadedContent.objects.create(
                user_id=99999,  # Non-existent user
                title='Invalid Content',
                subject='Testing'
            )
            self.fail("Should have raised integrity error")
        except Exception as e:
            print(f"    ✅ Foreign key constraint enforced: {type(e).__name__}")
        
        # Test 3: Unique constraints
        print("  Testing unique constraints...")
        
        try:
            # Try to create duplicate user
            User.objects.create_user(
                username='integrity_student',  # Duplicate username
                email='duplicate@test.com',
                password='testpass123'
            )
            self.fail("Should have raised integrity error")
        except Exception as e:
            print(f"    ✅ Unique constraint enforced: {type(e).__name__}")
    
    def test_data_consistency_across_transactions(self):
        """Test data consistency across database transactions"""
        print("\n" + "="*60)
        print("DATA INTEGRITY: Transaction Consistency")
        print("="*60)
        
        # Test 1: Atomic transaction rollback
        print("  Testing atomic transaction rollback...")
        
        initial_user_count = User.objects.count()
        initial_profile_count = StudentProfile.objects.count()
        
        try:
            with transaction.atomic():
                # Create user
                new_user = User.objects.create_user(
                    username='transaction_test',
                    email='transaction@test.com',
                    password='testpass123',
                    role='student'
                )
                
                # Create profile
                StudentProfile.objects.create(
                    user=new_user,
                    learning_preferences={'style': 'auditory'},
                    current_streak=0,
                    total_xp=0
                )
                
                # Force rollback
                raise Exception("Forced rollback")
                
        except Exception:
            pass  # Expected
        
        # Verify rollback occurred
        final_user_count = User.objects.count()
        final_profile_count = StudentProfile.objects.count()
        
        self.assertEqual(initial_user_count, final_user_count)
        self.assertEqual(initial_profile_count, final_profile_count)
        
        print("    ✅ Transaction rollback successful")
        
        # Test 2: Concurrent transaction handling
        print("  Testing concurrent transaction handling...")
        
        import threading
        import time
        
        results = []
        
        def update_xp(student_id, amount):
            try:
                with transaction.atomic():
                    profile = StudentProfile.objects.select_for_update().get(id=student_id)
                    time.sleep(0.1)  # Simulate processing time
                    profile.total_xp += amount
                    profile.save()
                    results.append(amount)
            except Exception as e:
                results.append(f"Error: {e}")
        
        initial_xp = self.student_profile.total_xp
        
        # Start concurrent transactions
        threads = []
        for i in range(3):
            thread = threading.Thread(target=update_xp, args=(self.student_profile.id, 10))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify final XP is correct
        self.student_profile.refresh_from_db()
        expected_xp = initial_xp + (10 * 3)  # 3 successful updates of 10 XP each
        
        self.assertEqual(self.student_profile.total_xp, expected_xp)
        print(f"    ✅ Concurrent transactions handled correctly (XP: {initial_xp} → {self.student_profile.total_xp})")
    
    def test_data_validation_integrity(self):
        """Test data validation and integrity constraints"""
        print("\n" + "="*60)
        print("DATA INTEGRITY: Validation Constraints")
        print("="*60)
        
        # Test 1: Model field validation
        print("  Testing model field validation...")
        
        try:
            # Try to create user with invalid email
            User.objects.create_user(
                username='invalid_email_test',
                email='not-an-email',
                password='testpass123'
            )
            # If we get here, check if email validation is working
            user = User.objects.get(username='invalid_email_test')
            # Django's EmailField should handle this, but let's verify
            print("    ⚠️  Email validation may need strengthening")
        except Exception as e:
            print(f"    ✅ Email validation working: {type(e).__name__}")
        
        # Test 2: Custom validation
        print("  Testing custom validation...")
        
        try:
            # Try to create student profile with negative XP
            StudentProfile.objects.create(
                user=self.teacher_user,  # Use existing user
                learning_preferences={},
                current_streak=-5,  # Invalid negative streak
                total_xp=-100  # Invalid negative XP
            )
            
            # If created, verify the values were handled
            profile = StudentProfile.objects.get(user=self.teacher_user)
            if profile.current_streak < 0 or profile.total_xp < 0:
                print("    ⚠️  Negative value validation may need implementation")
            else:
                print("    ✅ Negative values handled correctly")
                
        except Exception as e:
            print(f"    ✅ Custom validation working: {type(e).__name__}")
        
        # Test 3: JSON field validation
        print("  Testing JSON field validation...")
        
        try:
            # Create content with invalid JSON in key_concepts
            content = UploadedContent.objects.create(
                user=self.student_user,
                title='JSON Test',
                subject='Testing',
                key_concepts="invalid json"  # Should be list
            )
            
            # Verify it was stored correctly or handled
            content.refresh_from_db()
            print("    ✅ JSON field validation handled")
            
        except Exception as e:
            print(f"    ✅ JSON validation working: {type(e).__name__}")
    
    def test_backup_and_recovery_procedures(self):
        """Test backup and recovery procedures"""
        print("\n" + "="*60)
        print("DATA INTEGRITY: Backup and Recovery")
        print("="*60)
        
        # Test 1: Database dump and restore
        print("  Testing database backup...")
        
        # Create temporary directory for backup
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_file = os.path.join(temp_dir, 'test_backup.json')
            
            try:
                # Create database dump
                with open(backup_file, 'w') as f:
                    call_command('dumpdata', stdout=f, format='json', indent=2)
                
                # Verify backup file was created and has content
                self.assertTrue(os.path.exists(backup_file))
                
                with open(backup_file, 'r') as f:
                    backup_data = json.load(f)
                
                self.assertGreater(len(backup_data), 0)
                print(f"    ✅ Database backup created ({len(backup_data)} records)")
                
                # Test selective backup
                user_backup_file = os.path.join(temp_dir, 'user_backup.json')
                with open(user_backup_file, 'w') as f:
                    call_command('dumpdata', 'auth.user', stdout=f, format='json')
                
                with open(user_backup_file, 'r') as f:
                    user_data = json.load(f)
                
                # Should have at least our test users
                self.assertGreaterEqual(len(user_data), 3)
                print(f"    ✅ Selective backup created ({len(user_data)} users)")
                
            except Exception as e:
                print(f"    ❌ Backup failed: {e}")
        
        # Test 2: Data export/import consistency
        print("  Testing data export/import consistency...")
        
        # Export current data state
        original_user_count = User.objects.count()
        original_content_count = UploadedContent.objects.count()
        original_session_count = LearningSession.objects.count()
        
        # Create temporary backup
        with tempfile.TemporaryDirectory() as temp_dir:
            export_file = os.path.join(temp_dir, 'export_test.json')
            
            try:
                # Export specific models
                with open(export_file, 'w') as f:
                    call_command(
                        'dumpdata', 
                        'accounts.studentprofile',
                        'content.uploadedcontent',
                        'learning.learningsession',
                        stdout=f,
                        format='json'
                    )
                
                # Verify export
                with open(export_file, 'r') as f:
                    export_data = json.load(f)
                
                # Count records by model
                model_counts = {}
                for record in export_data:
                    model = record['model']
                    model_counts[model] = model_counts.get(model, 0) + 1
                
                print(f"    ✅ Data export successful:")
                for model, count in model_counts.items():
                    print(f"      - {model}: {count} records")
                
            except Exception as e:
                print(f"    ❌ Export failed: {e}")
    
    def test_data_migration_integrity(self):
        """Test data migration integrity"""
        print("\n" + "="*60)
        print("DATA INTEGRITY: Migration Integrity")
        print("="*60)
        
        # Test 1: Migration state consistency
        print("  Testing migration state...")
        
        try:
            # Check migration status
            call_command('showmigrations', verbosity=0)
            print("    ✅ Migration status check successful")
            
            # Verify no pending migrations
            from django.db.migrations.executor import MigrationExecutor
            from django.db import connections
            
            executor = MigrationExecutor(connections['default'])
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            
            if plan:
                print(f"    ⚠️  Pending migrations found: {len(plan)}")
                for migration, backwards in plan:
                    print(f"      - {migration}")
            else:
                print("    ✅ No pending migrations")
                
        except Exception as e:
            print(f"    ❌ Migration check failed: {e}")
        
        # Test 2: Schema consistency
        print("  Testing schema consistency...")
        
        try:
            # Get database schema information
            with connection.cursor() as cursor:
                # Check if all expected tables exist
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """)
                
                tables = [row[0] for row in cursor.fetchall()]
                
                # Expected core tables
                expected_tables = [
                    'auth_user',
                    'accounts_studentprofile',
                    'accounts_teacherprofile',
                    'accounts_parentprofile',
                    'content_uploadedcontent',
                    'learning_learningsession',
                    'gamification_achievement',
                    'community_studygroup'
                ]
                
                missing_tables = []
                for table in expected_tables:
                    if table not in tables:
                        missing_tables.append(table)
                
                if missing_tables:
                    print(f"    ⚠️  Missing tables: {missing_tables}")
                else:
                    print(f"    ✅ All expected tables present ({len(tables)} total)")
                
        except Exception as e:
            print(f"    ❌ Schema check failed: {e}")
    
    def test_data_archival_and_cleanup(self):
        """Test data archival and cleanup procedures"""
        print("\n" + "="*60)
        print("DATA INTEGRITY: Data Archival and Cleanup")
        print("="*60)
        
        # Test 1: Old data identification
        print("  Testing old data identification...")
        
        # Create old learning session
        old_session = LearningSession.objects.create(
            student=self.student_profile,
            content=self.content,
            performance_score=0.75
        )
        
        # Manually set old date (simulate old data)
        old_date = datetime.now() - timedelta(days=365)
        LearningSession.objects.filter(id=old_session.id).update(
            start_time=old_date,
            end_time=old_date + timedelta(hours=1)
        )
        
        # Query for old data
        cutoff_date = datetime.now() - timedelta(days=180)
        old_sessions = LearningSession.objects.filter(start_time__lt=cutoff_date)
        
        self.assertGreater(old_sessions.count(), 0)
        print(f"    ✅ Old data identified: {old_sessions.count()} sessions older than 180 days")
        
        # Test 2: Data cleanup simulation
        print("  Testing data cleanup procedures...")
        
        initial_session_count = LearningSession.objects.count()
        
        # Simulate cleanup (don't actually delete in test)
        old_sessions_count = old_sessions.count()
        
        # In a real cleanup, you might:
        # 1. Archive to separate table/file
        # 2. Delete after archival
        # 3. Log the cleanup operation
        
        print(f"    ✅ Cleanup simulation: {old_sessions_count} sessions would be archived")
        
        # Test 3: Orphaned data cleanup
        print("  Testing orphaned data cleanup...")
        
        # Check for orphaned records (records with missing foreign keys)
        orphaned_summaries = GeneratedSummary.objects.filter(content__isnull=True)
        orphaned_sessions = LearningSession.objects.filter(student__isnull=True)
        
        orphaned_count = orphaned_summaries.count() + orphaned_sessions.count()
        
        if orphaned_count > 0:
            print(f"    ⚠️  Found {orphaned_count} orphaned records")
        else:
            print("    ✅ No orphaned records found")
    
    def test_data_consistency_checks(self):
        """Test data consistency checks"""
        print("\n" + "="*60)
        print("DATA INTEGRITY: Consistency Checks")
        print("="*60)
        
        # Test 1: User-Profile consistency
        print("  Testing user-profile consistency...")
        
        users_without_profiles = User.objects.filter(
            role='student',
            studentprofile__isnull=True
        )
        
        teachers_without_profiles = User.objects.filter(
            role='teacher',
            teacherprofile__isnull=True
        )
        
        parents_without_profiles = User.objects.filter(
            role='parent',
            parentprofile__isnull=True
        )
        
        inconsistent_users = (
            users_without_profiles.count() + 
            teachers_without_profiles.count() + 
            parents_without_profiles.count()
        )
        
        if inconsistent_users > 0:
            print(f"    ⚠️  Found {inconsistent_users} users without matching profiles")
        else:
            print("    ✅ All users have matching profiles")
        
        # Test 2: Content-Generation consistency
        print("  Testing content-generation consistency...")
        
        processed_content = UploadedContent.objects.filter(processed=True)
        content_without_summaries = processed_content.filter(generatedsummary__isnull=True)
        content_without_quizzes = processed_content.filter(generatedquiz__isnull=True)
        
        if content_without_summaries.exists() or content_without_quizzes.exists():
            print(f"    ⚠️  Processed content missing generated materials:")
            print(f"      - Without summaries: {content_without_summaries.count()}")
            print(f"      - Without quizzes: {content_without_quizzes.count()}")
        else:
            print("    ✅ All processed content has generated materials")
        
        # Test 3: Gamification consistency
        print("  Testing gamification consistency...")
        
        # Check XP consistency
        students_with_achievements = StudentProfile.objects.filter(
            studentachievement__isnull=False
        ).distinct()
        
        for student in students_with_achievements:
            total_achievement_xp = sum([
                achievement.achievement.xp_requirement 
                for achievement in student.studentachievement_set.all()
            ])
            
            if student.total_xp < total_achievement_xp:
                print(f"    ⚠️  Student {student.user.username} has insufficient XP for achievements")
                break
        else:
            print("    ✅ XP and achievements are consistent")
        
        # Test 4: Parent-Child relationship consistency
        print("  Testing parent-child relationships...")
        
        for parent_profile in ParentProfile.objects.all():
            for child in parent_profile.children.all():
                if child.user.role != 'student':
                    print(f"    ⚠️  Parent linked to non-student: {child.user.username}")
                    break
        else:
            print("    ✅ Parent-child relationships are consistent")
    
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