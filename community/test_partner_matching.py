"""
Simple test script to verify study partner matching functionality
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import StudentProfile
from community.models import Subject, StudyPartnerRequest, StudyPartnership
from community.partner_services import StudyPartnerMatcher, StudyPartnerService

User = get_user_model()


class StudyPartnerMatchingTest(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create subjects
        self.math = Subject.objects.create(name="Mathematics", category="STEM")
        self.physics = Subject.objects.create(name="Physics", category="STEM")
        self.english = Subject.objects.create(name="English", category="Humanities")
        
        # Create users and student profiles
        self.user1 = User.objects.create_user(
            username="student1",
            email="student1@test.com",
            role="student"
        )
        self.student1 = StudentProfile.objects.create(
            user=self.user1,
            subjects_of_interest=["Mathematics", "Physics"],
            total_xp=500,
            current_streak=5
        )
        
        self.user2 = User.objects.create_user(
            username="student2",
            email="student2@test.com",
            role="student"
        )
        self.student2 = StudentProfile.objects.create(
            user=self.user2,
            subjects_of_interest=["Mathematics", "English"],
            total_xp=600,
            current_streak=3
        )
        
        self.user3 = User.objects.create_user(
            username="student3",
            email="student3@test.com",
            role="student"
        )
        self.student3 = StudentProfile.objects.create(
            user=self.user3,
            subjects_of_interest=["English"],
            total_xp=200,
            current_streak=1
        )
    
    def test_compatibility_calculation(self):
        """Test compatibility score calculation"""
        matcher = StudyPartnerMatcher()
        
        # Test compatibility between student1 and student2 (both interested in Math)
        score = matcher.calculate_compatibility_score(self.student1, self.student2, self.math)
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)
        
        # Test compatibility between student1 and student3 (no common subjects)
        score = matcher.calculate_compatibility_score(self.student1, self.student3)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_partner_recommendations(self):
        """Test getting partner recommendations"""
        matcher = StudyPartnerMatcher()
        
        # Get recommendations for student1
        recommendations = matcher.get_partner_recommendations(self.student1, limit=5)
        
        # Should return other students
        self.assertIsInstance(recommendations, list)
        self.assertLessEqual(len(recommendations), 2)  # Only 2 other students
        
        # Each recommendation should be a tuple of (student, score)
        for partner, score in recommendations:
            self.assertIsInstance(partner, StudentProfile)
            self.assertIsInstance(score, (int, float))
            self.assertNotEqual(partner, self.student1)  # Should not recommend self
    
    def test_send_partner_request(self):
        """Test sending a partner request"""
        service = StudyPartnerService()
        
        # Send request from student1 to student2
        request = service.send_partner_request(
            requester=self.student1,
            requested=self.student2,
            subject=self.math,
            message="Let's study math together!"
        )
        
        self.assertIsNotNone(request)
        self.assertEqual(request.requester, self.student1)
        self.assertEqual(request.requested, self.student2)
        self.assertEqual(request.subject, self.math)
        self.assertEqual(request.status, 'pending')
        
        # Try to send duplicate request - should return None
        duplicate_request = service.send_partner_request(
            requester=self.student1,
            requested=self.student2,
            subject=self.math
        )
        self.assertIsNone(duplicate_request)
    
    def test_accept_partner_request(self):
        """Test accepting a partner request"""
        service = StudyPartnerService()
        
        # Create a request
        request = StudyPartnerRequest.objects.create(
            requester=self.student1,
            requested=self.student2,
            subject=self.math,
            message="Let's study together!"
        )
        
        # Accept the request
        partnership = service.accept_partner_request(request)
        
        self.assertIsNotNone(partnership)
        self.assertEqual(partnership.student1, self.student1)
        self.assertEqual(partnership.student2, self.student2)
        self.assertEqual(partnership.subject, self.math)
        self.assertEqual(partnership.status, 'active')
        
        # Check that request status was updated
        request.refresh_from_db()
        self.assertEqual(request.status, 'accepted')
    
    def test_get_student_partnerships(self):
        """Test getting student partnerships"""
        service = StudyPartnerService()
        
        # Create a partnership
        partnership = StudyPartnership.objects.create(
            student1=self.student1,
            student2=self.student2,
            subject=self.math
        )
        
        # Get partnerships for student1
        partnerships = service.get_student_partnerships(self.student1)
        self.assertEqual(partnerships.count(), 1)
        self.assertEqual(partnerships.first(), partnership)
        
        # Get partnerships for student2
        partnerships = service.get_student_partnerships(self.student2)
        self.assertEqual(partnerships.count(), 1)
        self.assertEqual(partnerships.first(), partnership)
        
        # Get partnerships for student3 (should be empty)
        partnerships = service.get_student_partnerships(self.student3)
        self.assertEqual(partnerships.count(), 0)


if __name__ == '__main__':
    import django
    import os
    
    # Set up Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'metlab_edu.settings')
    django.setup()
    
    # Run the test
    import unittest
    unittest.main()