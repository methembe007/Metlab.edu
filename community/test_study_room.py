"""
Test cases for real-time study room functionality
"""
import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import StudentProfile
from .models import StudySession, StudyPartnership, Subject, StudyGroup, StudyGroupMembership

User = get_user_model()


# WebSocket tests are commented out due to import issues
# They can be enabled once the environment is properly configured


class StudyRoomViewTest(TestCase):
    """Test study room views and API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            role='student'
        )
        
        self.student = StudentProfile.objects.create(
            user=self.user,
            total_xp=1500,  # This will give level 5
            subjects_of_interest=['Math']
        )
        
        self.subject = Subject.objects.create(name='Math')
        
        # Create study group
        self.group = StudyGroup.objects.create(
            name='Test Group',
            subject=self.subject,
            created_by=self.student
        )
        
        # Add membership
        StudyGroupMembership.objects.create(
            study_group=self.group,
            student=self.student,
            role='admin'
        )
        
        # Create session
        self.session = StudySession.objects.create(
            study_group=self.group,
            session_type='group',
            title='Test Group Session',
            scheduled_time='2024-01-01 10:00:00',
            duration_minutes=60,
            created_by=self.student
        )
    
    def test_study_room_access(self):
        """Test study room view access"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(f'/community/study-room/{self.session.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Group Session')
        self.assertContains(response, 'Live Session')
    
    def test_unauthorized_study_room_access(self):
        """Test unauthorized access to study room"""
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@test.com',
            password='testpass123',
            role='student'
        )
        
        StudentProfile.objects.create(
            user=other_user,
            total_xp=600,  # This will give level 3
            subjects_of_interest=['Science']
        )
        
        self.client.login(username='otheruser', password='testpass123')
        
        response = self.client.get(f'/community/study-room/{self.session.id}/')
        self.assertEqual(response.status_code, 302)  # Redirect
    
    def test_report_issue_api(self):
        """Test study room issue reporting API"""
        self.client.login(username='testuser', password='testpass123')
        
        report_data = {
            'sessionId': self.session.id,
            'issueType': 'inappropriate_behavior',
            'description': 'Test report description'
        }
        
        response = self.client.post(
            '/community/api/study-room/report/',
            data=json.dumps(report_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertIn('reportId', response_data)