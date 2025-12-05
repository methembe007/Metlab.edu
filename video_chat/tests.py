from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import VideoSession, VideoSessionParticipant, VideoSessionEvent
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()


class VideoSessionModelTest(TestCase):
    """Test cases for VideoSession model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testteacher',
            email='teacher@test.com',
            password='testpass123'
        )
    
    def test_create_video_session(self):
        """Test creating a video session"""
        session = VideoSession.objects.create(
            session_type='one_on_one',
            host=self.user,
            title='Test Session',
            description='Test description',
            scheduled_time=timezone.now() + timedelta(hours=1)
        )
        
        self.assertIsNotNone(session.session_id)
        self.assertEqual(session.title, 'Test Session')
        self.assertEqual(session.host, self.user)
        self.assertEqual(session.status, 'scheduled')
        self.assertEqual(session.max_participants, 30)
        self.assertTrue(session.allow_screen_share)
    
    def test_video_session_str(self):
        """Test string representation of VideoSession"""
        session = VideoSession.objects.create(
            session_type='group',
            host=self.user,
            title='Group Session'
        )
        
        self.assertEqual(str(session), 'Group Session (Group Session)')


class VideoSessionParticipantModelTest(TestCase):
    """Test cases for VideoSessionParticipant model"""
    
    def setUp(self):
        self.host = User.objects.create_user(
            username='host',
            email='host@test.com',
            password='testpass123'
        )
        self.participant = User.objects.create_user(
            username='participant',
            email='participant@test.com',
            password='testpass123'
        )
        self.session = VideoSession.objects.create(
            session_type='one_on_one',
            host=self.host,
            title='Test Session'
        )
    
    def test_create_participant(self):
        """Test creating a session participant"""
        participant = VideoSessionParticipant.objects.create(
            session=self.session,
            user=self.participant,
            role='participant',
            status='invited'
        )
        
        self.assertEqual(participant.session, self.session)
        self.assertEqual(participant.user, self.participant)
        self.assertEqual(participant.status, 'invited')
        self.assertTrue(participant.audio_enabled)
        self.assertTrue(participant.video_enabled)
        self.assertFalse(participant.screen_sharing)
    
    def test_unique_participant_per_session(self):
        """Test that a user can only be added once to a session"""
        VideoSessionParticipant.objects.create(
            session=self.session,
            user=self.participant
        )
        
        # Attempting to add the same user again should raise an error
        with self.assertRaises(Exception):
            VideoSessionParticipant.objects.create(
                session=self.session,
                user=self.participant
            )


class VideoSessionEventModelTest(TestCase):
    """Test cases for VideoSessionEvent model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='user@test.com',
            password='testpass123'
        )
        self.session = VideoSession.objects.create(
            session_type='one_on_one',
            host=self.user,
            title='Test Session'
        )
    
    def test_create_event(self):
        """Test creating a session event"""
        event = VideoSessionEvent.objects.create(
            session=self.session,
            event_type='session_started',
            user=self.user,
            details={'message': 'Session started successfully'}
        )
        
        self.assertEqual(event.session, self.session)
        self.assertEqual(event.event_type, 'session_started')
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.details['message'], 'Session started successfully')
        self.assertIsNotNone(event.timestamp)
    
    def test_event_str(self):
        """Test string representation of VideoSessionEvent"""
        event = VideoSessionEvent.objects.create(
            session=self.session,
            event_type='participant_joined',
            user=self.user
        )
        
        self.assertEqual(str(event), f'Participant Joined - {self.session.title}')


from .services import VideoSessionService
from django.core.exceptions import ValidationError, PermissionDenied


class VideoSessionServiceTest(TestCase):
    """Test cases for VideoSessionService"""
    
    def setUp(self):
        self.host = User.objects.create_user(
            username='hostuser',
            email='host@test.com',
            password='testpass123'
        )
        self.participant = User.objects.create_user(
            username='participantuser',
            email='participant@test.com',
            password='testpass123'
        )
    
    def test_create_session(self):
        """Test creating a session through the service"""
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='one_on_one',
            title='Test One-on-One Session',
            description='Testing session creation'
        )
        
        self.assertIsNotNone(session)
        self.assertEqual(session.title, 'Test One-on-One Session')
        self.assertEqual(session.host, self.host)
        self.assertEqual(session.status, 'scheduled')
        
        # Verify host is added as participant
        host_participant = session.participants.filter(user=self.host, role='host').first()
        self.assertIsNotNone(host_participant)
        
        # Verify event was logged
        events = session.events.filter(event_type='session_started')
        self.assertEqual(events.count(), 1)
    
    def test_create_session_with_scheduled_time(self):
        """Test creating a scheduled session"""
        future_time = timezone.now() + timedelta(hours=2)
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='group',
            title='Scheduled Group Session',
            scheduled_time=future_time,
            duration_minutes=90
        )
        
        self.assertEqual(session.status, 'scheduled')
        self.assertEqual(session.scheduled_time, future_time)
        self.assertEqual(session.duration_minutes, 90)
    
    def test_create_session_invalid_type(self):
        """Test creating a session with invalid type"""
        with self.assertRaises(ValidationError):
            VideoSessionService.create_session(
                host=self.host,
                session_type='invalid_type',
                title='Invalid Session'
            )
    
    def test_schedule_session(self):
        """Test scheduling a session"""
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='class',
            title='Class Session'
        )
        
        future_time = timezone.now() + timedelta(days=1)
        updated_session = VideoSessionService.schedule_session(
            session_id=session.session_id,
            scheduled_time=future_time,
            user=self.host
        )
        
        self.assertEqual(updated_session.scheduled_time, future_time)
        self.assertEqual(updated_session.status, 'scheduled')
    
    def test_schedule_session_past_time(self):
        """Test scheduling a session with past time fails"""
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='one_on_one',
            title='Test Session'
        )
        
        past_time = timezone.now() - timedelta(hours=1)
        with self.assertRaises(ValidationError):
            VideoSessionService.schedule_session(
                session_id=session.session_id,
                scheduled_time=past_time
            )
    
    def test_start_session(self):
        """Test starting a session"""
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='one_on_one',
            title='Test Session'
        )
        
        started_session = VideoSessionService.start_session(
            session_id=session.session_id,
            user=self.host
        )
        
        self.assertEqual(started_session.status, 'active')
        self.assertIsNotNone(started_session.started_at)
        
        # Verify event was logged
        events = started_session.events.filter(event_type='session_started')
        self.assertGreaterEqual(events.count(), 1)
    
    def test_start_session_non_host(self):
        """Test that non-host cannot start session"""
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='one_on_one',
            title='Test Session'
        )
        
        with self.assertRaises(PermissionDenied):
            VideoSessionService.start_session(
                session_id=session.session_id,
                user=self.participant
            )
    
    def test_end_session(self):
        """Test ending a session"""
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='group',
            title='Test Session'
        )
        
        # Start the session first
        VideoSessionService.start_session(
            session_id=session.session_id,
            user=self.host
        )
        
        # End the session
        ended_session = VideoSessionService.end_session(
            session_id=session.session_id,
            user=self.host
        )
        
        self.assertEqual(ended_session.status, 'completed')
        self.assertIsNotNone(ended_session.ended_at)
        
        # Verify event was logged
        events = ended_session.events.filter(event_type='session_ended')
        self.assertEqual(events.count(), 1)
    
    def test_end_session_non_host(self):
        """Test that non-host cannot end session"""
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='one_on_one',
            title='Test Session'
        )
        
        VideoSessionService.start_session(
            session_id=session.session_id,
            user=self.host
        )
        
        with self.assertRaises(PermissionDenied):
            VideoSessionService.end_session(
                session_id=session.session_id,
                user=self.participant
            )
    
    def test_cancel_session(self):
        """Test cancelling a scheduled session"""
        future_time = timezone.now() + timedelta(hours=2)
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='class',
            title='Test Session',
            scheduled_time=future_time
        )
        
        cancelled_session = VideoSessionService.cancel_session(
            session_id=session.session_id,
            user=self.host,
            reason='Testing cancellation'
        )
        
        self.assertEqual(cancelled_session.status, 'cancelled')
        
        # Verify event was logged
        events = cancelled_session.events.filter(event_type='session_ended')
        self.assertEqual(events.count(), 1)
    
    def test_cancel_active_session_fails(self):
        """Test that active sessions cannot be cancelled"""
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='one_on_one',
            title='Test Session'
        )
        
        VideoSessionService.start_session(
            session_id=session.session_id,
            user=self.host
        )
        
        with self.assertRaises(ValidationError):
            VideoSessionService.cancel_session(
                session_id=session.session_id,
                user=self.host
            )
    
    def test_get_session(self):
        """Test retrieving a session"""
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='group',
            title='Test Session'
        )
        
        retrieved_session = VideoSessionService.get_session(session.session_id)
        
        self.assertEqual(retrieved_session.session_id, session.session_id)
        self.assertEqual(retrieved_session.title, session.title)
    
    def test_get_user_sessions(self):
        """Test getting all sessions for a user"""
        # Create multiple sessions
        session1 = VideoSessionService.create_session(
            host=self.host,
            session_type='one_on_one',
            title='Session 1'
        )
        
        session2 = VideoSessionService.create_session(
            host=self.host,
            session_type='group',
            title='Session 2'
        )
        
        sessions = VideoSessionService.get_user_sessions(self.host)
        
        self.assertEqual(sessions.count(), 2)
        self.assertIn(session1, sessions)
        self.assertIn(session2, sessions)
    
    def test_get_user_sessions_filtered_by_status(self):
        """Test getting user sessions filtered by status"""
        session1 = VideoSessionService.create_session(
            host=self.host,
            session_type='one_on_one',
            title='Scheduled Session'
        )
        
        session2 = VideoSessionService.create_session(
            host=self.host,
            session_type='group',
            title='Active Session'
        )
        VideoSessionService.start_session(session2.session_id, self.host)
        
        scheduled_sessions = VideoSessionService.get_user_sessions(
            self.host, 
            status='scheduled'
        )
        active_sessions = VideoSessionService.get_user_sessions(
            self.host, 
            status='active'
        )
        
        self.assertEqual(scheduled_sessions.count(), 1)
        self.assertEqual(active_sessions.count(), 1)
        self.assertIn(session1, scheduled_sessions)
        self.assertIn(session2, active_sessions)


class ParticipantManagementTest(TestCase):
    """Test cases for participant management functionality"""
    
    def setUp(self):
        self.host = User.objects.create_user(
            username='host',
            email='host@test.com',
            password='testpass123'
        )
        self.student1 = User.objects.create_user(
            username='student1',
            email='student1@test.com',
            password='testpass123'
        )
        self.student2 = User.objects.create_user(
            username='student2',
            email='student2@test.com',
            password='testpass123'
        )
        self.student3 = User.objects.create_user(
            username='student3',
            email='student3@test.com',
            password='testpass123'
        )
    
    def test_join_session(self):
        """Test participant joining a session"""
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='group',
            title='Test Session'
        )
        VideoSessionService.start_session(session.session_id, self.host)
        
        participant = VideoSessionService.join_session(
            session_id=session.session_id,
            user=self.student1
        )
        
        self.assertEqual(participant.user, self.student1)
        self.assertEqual(participant.status, 'joined')
        self.assertEqual(participant.role, 'participant')
        self.assertIsNotNone(participant.joined_at)
        
        # Verify event was logged
        events = session.events.filter(event_type='participant_joined')
        self.assertEqual(events.count(), 1)
    
    def test_join_session_participant_limit(self):
        """Test that participant limit is enforced"""
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='group',
            title='Limited Session',
            max_participants=2
        )
        VideoSessionService.start_session(session.session_id, self.host)
        
        # Host is already a participant, so only 1 more can join
        VideoSessionService.join_session(session.session_id, self.student1)
        
        # Second student should not be able to join
        with self.assertRaises(ValidationError) as context:
            VideoSessionService.join_session(session.session_id, self.student2)
        
        self.assertIn('maximum capacity', str(context.exception))
    
    def test_join_session_busy_status(self):
        """Test that user cannot join if already in another active session"""
        session1 = VideoSessionService.create_session(
            host=self.host,
            session_type='one_on_one',
            title='Session 1'
        )
        VideoSessionService.start_session(session1.session_id, self.host)
        VideoSessionService.join_session(session1.session_id, self.student1)
        
        session2 = VideoSessionService.create_session(
            host=self.host,
            session_type='one_on_one',
            title='Session 2'
        )
        VideoSessionService.start_session(session2.session_id, self.host)
        
        # Student1 should not be able to join session2 while in session1
        with self.assertRaises(ValidationError) as context:
            VideoSessionService.join_session(session2.session_id, self.student1)
        
        self.assertIn('already in an active session', str(context.exception))
    
    def test_join_completed_session_fails(self):
        """Test that users cannot join completed sessions"""
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='group',
            title='Test Session'
        )
        VideoSessionService.start_session(session.session_id, self.host)
        VideoSessionService.end_session(session.session_id, self.host)
        
        with self.assertRaises(ValidationError) as context:
            VideoSessionService.join_session(session.session_id, self.student1)
        
        self.assertIn('completed', str(context.exception))
    
    def test_leave_session(self):
        """Test participant leaving a session"""
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='group',
            title='Test Session'
        )
        VideoSessionService.start_session(session.session_id, self.host)
        VideoSessionService.join_session(session.session_id, self.student1)
        
        participant = VideoSessionService.leave_session(
            session_id=session.session_id,
            user=self.student1
        )
        
        self.assertEqual(participant.status, 'left')
        self.assertIsNotNone(participant.left_at)
        self.assertFalse(participant.audio_enabled)
        self.assertFalse(participant.video_enabled)
        self.assertFalse(participant.screen_sharing)
        
        # Verify event was logged
        events = session.events.filter(event_type='participant_left')
        self.assertEqual(events.count(), 1)
    
    def test_leave_session_not_joined(self):
        """Test that user cannot leave if not joined"""
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='group',
            title='Test Session'
        )
        
        with self.assertRaises(VideoSessionParticipant.DoesNotExist):
            VideoSessionService.leave_session(session.session_id, self.student1)
    
    def test_rejoin_session_after_leaving(self):
        """Test that participant can rejoin after leaving"""
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='group',
            title='Test Session'
        )
        VideoSessionService.start_session(session.session_id, self.host)
        
        # Join, leave, then rejoin
        VideoSessionService.join_session(session.session_id, self.student1)
        VideoSessionService.leave_session(session.session_id, self.student1)
        participant = VideoSessionService.join_session(session.session_id, self.student1)
        
        self.assertEqual(participant.status, 'joined')
        self.assertIsNotNone(participant.joined_at)
        self.assertIsNone(participant.left_at)
    
    def test_remove_participant(self):
        """Test host removing a participant"""
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='group',
            title='Test Session'
        )
        VideoSessionService.start_session(session.session_id, self.host)
        VideoSessionService.join_session(session.session_id, self.student1)
        
        participant = VideoSessionService.remove_participant(
            session_id=session.session_id,
            user_to_remove=self.student1,
            removed_by=self.host
        )
        
        self.assertEqual(participant.status, 'removed')
        self.assertIsNotNone(participant.left_at)
        self.assertFalse(participant.audio_enabled)
        self.assertFalse(participant.video_enabled)
        
        # Verify event was logged
        events = session.events.filter(event_type='participant_left')
        removal_events = [e for e in events if e.details.get('action') == 'participant_removed']
        self.assertEqual(len(removal_events), 1)
    
    def test_remove_participant_non_host(self):
        """Test that non-host cannot remove participants"""
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='group',
            title='Test Session'
        )
        VideoSessionService.start_session(session.session_id, self.host)
        VideoSessionService.join_session(session.session_id, self.student1)
        VideoSessionService.join_session(session.session_id, self.student2)
        
        with self.assertRaises(PermissionDenied):
            VideoSessionService.remove_participant(
                session_id=session.session_id,
                user_to_remove=self.student2,
                removed_by=self.student1
            )
    
    def test_cannot_remove_host(self):
        """Test that host cannot be removed"""
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='group',
            title='Test Session'
        )
        
        with self.assertRaises(ValidationError) as context:
            VideoSessionService.remove_participant(
                session_id=session.session_id,
                user_to_remove=self.host,
                removed_by=self.host
            )
        
        self.assertIn('Cannot remove the session host', str(context.exception))
    
    def test_removed_participant_cannot_rejoin(self):
        """Test that removed participants cannot rejoin"""
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='group',
            title='Test Session'
        )
        VideoSessionService.start_session(session.session_id, self.host)
        VideoSessionService.join_session(session.session_id, self.student1)
        VideoSessionService.remove_participant(
            session.session_id, self.student1, self.host
        )
        
        with self.assertRaises(PermissionDenied) as context:
            VideoSessionService.join_session(session.session_id, self.student1)
        
        self.assertIn('removed from this session', str(context.exception))
    
    def test_get_session_participants(self):
        """Test getting all participants in a session"""
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='group',
            title='Test Session'
        )
        VideoSessionService.start_session(session.session_id, self.host)
        VideoSessionService.join_session(session.session_id, self.student1)
        VideoSessionService.join_session(session.session_id, self.student2)
        
        participants = VideoSessionService.get_session_participants(session.session_id)
        
        # Should include host + 2 students
        self.assertEqual(participants.count(), 3)
    
    def test_get_session_participants_filtered(self):
        """Test getting participants filtered by status"""
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='group',
            title='Test Session'
        )
        VideoSessionService.start_session(session.session_id, self.host)
        VideoSessionService.join_session(session.session_id, self.host)  # Host needs to join
        VideoSessionService.join_session(session.session_id, self.student1)
        VideoSessionService.join_session(session.session_id, self.student2)
        VideoSessionService.leave_session(session.session_id, self.student2)
        
        joined_participants = VideoSessionService.get_session_participants(
            session.session_id, status_filter='joined'
        )
        left_participants = VideoSessionService.get_session_participants(
            session.session_id, status_filter='left'
        )
        
        self.assertEqual(joined_participants.count(), 2)  # host + student1
        self.assertEqual(left_participants.count(), 1)  # student2
    
    def test_is_user_busy(self):
        """Test checking if user is busy in another session"""
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='one_on_one',
            title='Test Session'
        )
        VideoSessionService.start_session(session.session_id, self.host)
        VideoSessionService.join_session(session.session_id, self.student1)
        
        is_busy, active_session = VideoSessionService.is_user_busy(self.student1)
        
        self.assertTrue(is_busy)
        self.assertEqual(active_session.session_id, session.session_id)
        
        # Student2 is not busy
        is_busy2, active_session2 = VideoSessionService.is_user_busy(self.student2)
        self.assertFalse(is_busy2)
        self.assertIsNone(active_session2)
    
    def test_update_participant_media_state(self):
        """Test updating participant media state"""
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='group',
            title='Test Session'
        )
        VideoSessionService.start_session(session.session_id, self.host)
        VideoSessionService.join_session(session.session_id, self.student1)
        
        participant = VideoSessionService.update_participant_media_state(
            session_id=session.session_id,
            user=self.student1,
            audio_enabled=False,
            video_enabled=False
        )
        
        self.assertFalse(participant.audio_enabled)
        self.assertFalse(participant.video_enabled)
    
    def test_update_screen_sharing_logs_events(self):
        """Test that screen sharing updates log events"""
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='group',
            title='Test Session'
        )
        VideoSessionService.start_session(session.session_id, self.host)
        VideoSessionService.join_session(session.session_id, self.student1)
        
        # Start screen sharing
        VideoSessionService.update_participant_media_state(
            session_id=session.session_id,
            user=self.student1,
            screen_sharing=True
        )
        
        start_events = session.events.filter(event_type='screen_share_started')
        self.assertEqual(start_events.count(), 1)
        
        # Stop screen sharing
        VideoSessionService.update_participant_media_state(
            session_id=session.session_id,
            user=self.student1,
            screen_sharing=False
        )
        
        stop_events = session.events.filter(event_type='screen_share_stopped')
        self.assertEqual(stop_events.count(), 1)


class SessionHistoryAndLoggingTest(TestCase):
    """Test cases for session history and logging functionality"""
    
    def setUp(self):
        self.host = User.objects.create_user(
            username='host',
            email='host@test.com',
            password='testpass123'
        )
        self.student1 = User.objects.create_user(
            username='student1',
            email='student1@test.com',
            password='testpass123'
        )
        self.student2 = User.objects.create_user(
            username='student2',
            email='student2@test.com',
            password='testpass123'
        )
    
    def test_get_session_history(self):
        """Test retrieving session history for a user"""
        # Create multiple sessions
        session1 = VideoSessionService.create_session(
            host=self.host,
            session_type='one_on_one',
            title='Session 1'
        )
        
        session2 = VideoSessionService.create_session(
            host=self.host,
            session_type='group',
            title='Session 2'
        )
        
        # Get history
        history = VideoSessionService.get_session_history(self.host)
        
        self.assertEqual(history.count(), 2)
        self.assertIn(session1, history)
        self.assertIn(session2, history)
    
    def test_get_session_history_with_date_filter(self):
        """Test retrieving session history with date filters"""
        # Create sessions at different times
        past_time = timezone.now() - timedelta(days=7)
        
        # Create an old session (we'll manually set created_at)
        session1 = VideoSessionService.create_session(
            host=self.host,
            session_type='one_on_one',
            title='Old Session'
        )
        VideoSession.objects.filter(session_id=session1.session_id).update(
            created_at=past_time
        )
        
        # Create a recent session
        session2 = VideoSessionService.create_session(
            host=self.host,
            session_type='group',
            title='Recent Session'
        )
        
        # Get history from 3 days ago
        start_date = timezone.now() - timedelta(days=3)
        history = VideoSessionService.get_session_history(
            self.host,
            start_date=start_date
        )
        
        self.assertEqual(history.count(), 1)
        self.assertIn(session2, history)
        self.assertNotIn(session1, history)
    
    def test_get_session_history_with_limit(self):
        """Test retrieving session history with limit"""
        # Create multiple sessions
        for i in range(5):
            VideoSessionService.create_session(
                host=self.host,
                session_type='group',
                title=f'Session {i+1}'
            )
        
        # Get history with limit
        history = VideoSessionService.get_session_history(self.host, limit=3)
        
        self.assertEqual(history.count(), 3)
    
    def test_get_session_events(self):
        """Test retrieving all events for a session"""
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='group',
            title='Test Session'
        )
        VideoSessionService.start_session(session.session_id, self.host)
        VideoSessionService.join_session(session.session_id, self.student1)
        VideoSessionService.leave_session(session.session_id, self.student1)
        
        events = VideoSessionService.get_session_events(session.session_id)
        
        # Should have: session_created, session_started, participant_joined, participant_left
        self.assertGreaterEqual(events.count(), 3)
    
    def test_get_session_events_filtered(self):
        """Test retrieving filtered events for a session"""
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='group',
            title='Test Session'
        )
        VideoSessionService.start_session(session.session_id, self.host)
        VideoSessionService.join_session(session.session_id, self.student1)
        VideoSessionService.join_session(session.session_id, self.student2)
        
        # Get only participant_joined events
        join_events = VideoSessionService.get_session_events(
            session.session_id,
            event_type='participant_joined'
        )
        
        self.assertEqual(join_events.count(), 2)
    
    def test_log_event(self):
        """Test logging a custom event"""
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='one_on_one',
            title='Test Session'
        )
        
        event = VideoSessionService.log_event(
            session_id=session.session_id,
            event_type='connection_issue',
            user=self.student1,
            details={'reason': 'Network timeout', 'severity': 'warning'}
        )
        
        self.assertEqual(event.event_type, 'connection_issue')
        self.assertEqual(event.user, self.student1)
        self.assertEqual(event.details['reason'], 'Network timeout')
    
    def test_log_event_invalid_type(self):
        """Test that logging invalid event type raises error"""
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='one_on_one',
            title='Test Session'
        )
        
        with self.assertRaises(ValidationError):
            VideoSessionService.log_event(
                session_id=session.session_id,
                event_type='invalid_event_type',
                user=self.student1
            )
    
    def test_get_session_statistics(self):
        """Test getting detailed statistics for a session"""
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='group',
            title='Test Session'
        )
        VideoSessionService.start_session(session.session_id, self.host)
        VideoSessionService.join_session(session.session_id, self.host)
        VideoSessionService.join_session(session.session_id, self.student1)
        VideoSessionService.join_session(session.session_id, self.student2)
        
        # Simulate some time passing
        import time
        time.sleep(0.1)
        
        VideoSessionService.leave_session(session.session_id, self.student1)
        VideoSessionService.end_session(session.session_id, self.host)
        
        stats = VideoSessionService.get_session_statistics(session.session_id)
        
        self.assertEqual(stats['session_id'], str(session.session_id))
        self.assertEqual(stats['title'], 'Test Session')
        self.assertEqual(stats['status'], 'completed')
        self.assertEqual(stats['participants']['total'], 3)
        self.assertIsNotNone(stats['duration_minutes'])
        self.assertIn('events', stats)
        self.assertIn('features_used', stats)
    
    def test_get_child_session_summary(self):
        """Test getting session summary for a child"""
        # Create and complete a session
        session = VideoSessionService.create_session(
            host=self.host,
            session_type='one_on_one',
            title='Tutoring Session'
        )
        VideoSessionService.start_session(session.session_id, self.host)
        
        # Join the host first
        VideoSessionService.join_session(session.session_id, self.host)
        
        # Join the student
        participant = VideoSessionService.join_session(session.session_id, self.student1)
        
        # Manually set joined_at to ensure we have a time difference
        from django.utils import timezone
        from datetime import timedelta
        participant.joined_at = timezone.now() - timedelta(minutes=5)
        participant.save()
        
        VideoSessionService.leave_session(session.session_id, self.student1)
        VideoSessionService.end_session(session.session_id, self.host)
        
        summary = VideoSessionService.get_child_session_summary(self.student1)
        
        self.assertEqual(summary['total_sessions'], 1)
        self.assertEqual(summary['completed_sessions'], 1)
        self.assertGreater(summary['total_participation_minutes'], 0)
        self.assertIn('one_on_one', summary['sessions_by_type'])
        self.assertIn(self.host.username, summary['teachers_interacted'])


from accounts.models import ParentProfile, StudentProfile


class ParentMonitoringTest(TestCase):
    """Test cases for parent monitoring functionality"""
    
    def setUp(self):
        # Create parent user
        self.parent_user = User.objects.create_user(
            username='parent',
            email='parent@test.com',
            password='testpass123'
        )
        
        # Create parent profile
        self.parent_profile = ParentProfile.objects.create(
            user=self.parent_user
        )
        
        # Create child users
        self.child1 = User.objects.create_user(
            username='child1',
            email='child1@test.com',
            password='testpass123'
        )
        
        self.child2 = User.objects.create_user(
            username='child2',
            email='child2@test.com',
            password='testpass123'
        )
        
        # Create student profiles for children
        self.child1_profile = StudentProfile.objects.create(
            user=self.child1,
            grade_level=5
        )
        
        self.child2_profile = StudentProfile.objects.create(
            user=self.child2,
            grade_level=6
        )
        
        # Link children to parent (ParentProfile.children is a ManyToMany to StudentProfile)
        self.parent_profile.children.add(self.child1_profile, self.child2_profile)
        
        # Create teacher
        self.teacher = User.objects.create_user(
            username='teacher',
            email='teacher@test.com',
            password='testpass123'
        )
    
    def test_get_parent_monitoring_data(self):
        """Test retrieving monitoring data for parent"""
        # Create sessions with children
        session1 = VideoSessionService.create_session(
            host=self.teacher,
            session_type='one_on_one',
            title='Math Tutoring'
        )
        VideoSessionService.start_session(session1.session_id, self.teacher)
        VideoSessionService.join_session(session1.session_id, self.child1)
        
        session2 = VideoSessionService.create_session(
            host=self.teacher,
            session_type='group',
            title='Science Class'
        )
        VideoSessionService.start_session(session2.session_id, self.teacher)
        VideoSessionService.join_session(session2.session_id, self.child2)
        
        # Get monitoring data
        data = VideoSessionService.get_parent_monitoring_data(self.parent_user)
        
        self.assertEqual(len(data['sessions']), 2)
        self.assertEqual(data['statistics']['total_sessions'], 2)
        self.assertEqual(len(data['children']), 2)
        self.assertIn(self.teacher.username, data['statistics']['unique_teachers'])
    
    def test_get_parent_monitoring_data_specific_child(self):
        """Test retrieving monitoring data for specific child"""
        # Create sessions
        session1 = VideoSessionService.create_session(
            host=self.teacher,
            session_type='one_on_one',
            title='Child1 Session'
        )
        VideoSessionService.start_session(session1.session_id, self.teacher)
        VideoSessionService.join_session(session1.session_id, self.child1)
        
        session2 = VideoSessionService.create_session(
            host=self.teacher,
            session_type='one_on_one',
            title='Child2 Session'
        )
        VideoSessionService.start_session(session2.session_id, self.teacher)
        VideoSessionService.join_session(session2.session_id, self.child2)
        
        # Get monitoring data for child1 only
        data = VideoSessionService.get_parent_monitoring_data(
            self.parent_user,
            child_user=self.child1
        )
        
        self.assertEqual(len(data['sessions']), 1)
        self.assertEqual(data['sessions'][0]['title'], 'Child1 Session')
        self.assertEqual(len(data['children']), 1)
    
    def test_get_parent_monitoring_data_with_date_filter(self):
        """Test retrieving monitoring data with date filters"""
        # Create an old session
        past_time = timezone.now() - timedelta(days=10)
        session1 = VideoSessionService.create_session(
            host=self.teacher,
            session_type='one_on_one',
            title='Old Session'
        )
        VideoSession.objects.filter(session_id=session1.session_id).update(
            created_at=past_time
        )
        VideoSessionService.join_session(session1.session_id, self.child1)
        
        # Create a recent session
        session2 = VideoSessionService.create_session(
            host=self.teacher,
            session_type='one_on_one',
            title='Recent Session'
        )
        VideoSessionService.join_session(session2.session_id, self.child1)
        
        # Get monitoring data from 5 days ago
        start_date = timezone.now() - timedelta(days=5)
        data = VideoSessionService.get_parent_monitoring_data(
            self.parent_user,
            start_date=start_date
        )
        
        self.assertEqual(len(data['sessions']), 1)
        self.assertEqual(data['sessions'][0]['title'], 'Recent Session')
    
    def test_get_parent_monitoring_data_no_parent_profile(self):
        """Test that non-parent users cannot access monitoring data"""
        regular_user = User.objects.create_user(
            username='regular',
            email='regular@test.com',
            password='testpass123'
        )
        
        with self.assertRaises(PermissionDenied):
            VideoSessionService.get_parent_monitoring_data(regular_user)
    
    def test_get_parent_monitoring_data_unlinked_child(self):
        """Test that parent cannot access data for unlinked child"""
        unlinked_child = User.objects.create_user(
            username='unlinked',
            email='unlinked@test.com',
            password='testpass123'
        )
        
        with self.assertRaises(PermissionDenied):
            VideoSessionService.get_parent_monitoring_data(
                self.parent_user,
                child_user=unlinked_child
            )
    
    def test_parent_monitoring_includes_session_details(self):
        """Test that monitoring data includes detailed session information"""
        session = VideoSessionService.create_session(
            host=self.teacher,
            session_type='one_on_one',
            title='Test Session'
        )
        VideoSessionService.start_session(session.session_id, self.teacher)
        VideoSessionService.join_session(session.session_id, self.child1)
        
        # Simulate some time passing
        import time
        time.sleep(0.1)
        
        VideoSessionService.leave_session(session.session_id, self.child1)
        VideoSessionService.end_session(session.session_id, self.teacher)
        
        data = VideoSessionService.get_parent_monitoring_data(self.parent_user)
        
        session_info = data['sessions'][0]
        self.assertEqual(session_info['title'], 'Test Session')
        self.assertEqual(session_info['host'], self.teacher.username)
        self.assertEqual(session_info['status'], 'completed')
        self.assertIsNotNone(session_info['duration_minutes'])
        self.assertEqual(len(session_info['child_participants']), 1)
        self.assertEqual(session_info['child_participants'][0]['username'], self.child1.username)
    
    def test_parent_monitoring_statistics(self):
        """Test that monitoring data includes accurate statistics"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Create multiple sessions
        for i in range(3):
            session = VideoSessionService.create_session(
                host=self.teacher,
                session_type='group',
                title=f'Session {i+1}'
            )
            
            VideoSessionService.start_session(session.session_id, self.teacher)
            
            # Manually set started_at to ensure we have time differences
            session.refresh_from_db()
            session.started_at = timezone.now() - timedelta(minutes=10)
            session.save()
            
            VideoSessionService.join_session(session.session_id, self.child1)
            VideoSessionService.leave_session(session.session_id, self.child1)
            VideoSessionService.end_session(session.session_id, self.teacher)
        
        data = VideoSessionService.get_parent_monitoring_data(self.parent_user)
        
        self.assertEqual(data['statistics']['total_sessions'], 3)
        self.assertGreater(data['statistics']['total_duration_minutes'], 0)
        self.assertEqual(data['statistics']['sessions_by_type']['group'], 3)
        self.assertIn(self.teacher.username, data['statistics']['unique_teachers'])
