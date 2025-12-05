"""
Notification service for video chat sessions.
Handles calendar entries, reminders, and session notifications.
Requirements: 5.2, 5.3, 5.4, 5.5
"""
import logging
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.template.loader import render_to_string
from datetime import timedelta
from .models import VideoSession, VideoSessionParticipant

logger = logging.getLogger(__name__)


class VideoSessionNotificationService:
    """Service for managing video session notifications"""
    
    @staticmethod
    def send_session_scheduled_notification(session, participants=None):
        """
        Send notification when a session is scheduled.
        Creates calendar entries for participants.
        Requirements: 5.2
        
        Args:
            session: VideoSession instance
            participants: Optional list of User objects (if None, notifies all participants)
        """
        if participants is None:
            # Get all invited participants except the host
            participant_records = VideoSessionParticipant.objects.filter(
                session=session,
                status='invited'
            ).exclude(user=session.host).select_related('user')
            participants = [p.user for p in participant_records]
        
        if not participants:
            logger.info(f"No participants to notify for session {session.session_id}")
            return
        
        # Generate session URL
        session_url = f"{settings.SITE_URL}{reverse('video_chat:session_detail', kwargs={'session_id': session.session_id})}"
        
        # Prepare email context
        context = {
            'session': session,
            'session_url': session_url,
            'host': session.host,
        }
        
        # Send email to each participant
        for participant in participants:
            try:
                # Render email content
                subject = f"Video Session Scheduled: {session.title}"
                html_message = render_to_string('video_chat/emails/session_scheduled.html', {
                    **context,
                    'participant': participant,
                })
                plain_message = render_to_string('video_chat/emails/session_scheduled.txt', {
                    **context,
                    'participant': participant,
                })
                
                # Send email
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[participant.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                logger.info(f"Sent session scheduled notification to {participant.email}")
                
            except Exception as e:
                logger.error(f"Error sending notification to {participant.email}: {str(e)}")
    
    @staticmethod
    def send_session_reminder(session):
        """
        Send reminder notification 15 minutes before session.
        Requirements: 5.3
        
        Args:
            session: VideoSession instance
        """
        # Get all invited participants
        participant_records = VideoSessionParticipant.objects.filter(
            session=session,
            status='invited'
        ).select_related('user')
        
        if not participant_records:
            logger.info(f"No participants to remind for session {session.session_id}")
            return
        
        # Generate join URL
        join_url = f"{settings.SITE_URL}{reverse('video_chat:join_session', kwargs={'session_id': session.session_id})}"
        
        # Prepare email context
        context = {
            'session': session,
            'join_url': join_url,
            'host': session.host,
            'minutes_until': 15,
        }
        
        # Send reminder to each participant
        for participant_record in participant_records:
            participant = participant_record.user
            
            try:
                # Render email content
                subject = f"Reminder: Video Session Starting Soon - {session.title}"
                html_message = render_to_string('video_chat/emails/session_reminder.html', {
                    **context,
                    'participant': participant,
                })
                plain_message = render_to_string('video_chat/emails/session_reminder.txt', {
                    **context,
                    'participant': participant,
                })
                
                # Send email
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[participant.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                logger.info(f"Sent session reminder to {participant.email}")
                
            except Exception as e:
                logger.error(f"Error sending reminder to {participant.email}: {str(e)}")
    
    @staticmethod
    def send_session_started_notification(session):
        """
        Send notification when a session starts.
        Requirements: 5.4
        
        Args:
            session: VideoSession instance
        """
        # Get all invited participants who haven't joined yet
        participant_records = VideoSessionParticipant.objects.filter(
            session=session,
            status='invited'
        ).select_related('user')
        
        if not participant_records:
            return
        
        # Generate join URL
        join_url = f"{settings.SITE_URL}{reverse('video_chat:join_session', kwargs={'session_id': session.session_id})}"
        
        # Prepare email context
        context = {
            'session': session,
            'join_url': join_url,
            'host': session.host,
        }
        
        # Send notification to each participant
        for participant_record in participant_records:
            participant = participant_record.user
            
            try:
                # Render email content
                subject = f"Video Session Started: {session.title}"
                html_message = render_to_string('video_chat/emails/session_started.html', {
                    **context,
                    'participant': participant,
                })
                plain_message = render_to_string('video_chat/emails/session_started.txt', {
                    **context,
                    'participant': participant,
                })
                
                # Send email
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[participant.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                logger.info(f"Sent session started notification to {participant.email}")
                
            except Exception as e:
                logger.error(f"Error sending notification to {participant.email}: {str(e)}")
    
    @staticmethod
    def send_session_cancelled_notification(session, reason=''):
        """
        Send notification when a session is cancelled.
        Requirements: 5.2
        
        Args:
            session: VideoSession instance
            reason: Optional cancellation reason
        """
        # Get all invited participants
        participant_records = VideoSessionParticipant.objects.filter(
            session=session
        ).exclude(user=session.host).select_related('user')
        
        if not participant_records:
            return
        
        # Prepare email context
        context = {
            'session': session,
            'host': session.host,
            'reason': reason,
        }
        
        # Send notification to each participant
        for participant_record in participant_records:
            participant = participant_record.user
            
            try:
                # Render email content
                subject = f"Video Session Cancelled: {session.title}"
                html_message = render_to_string('video_chat/emails/session_cancelled.html', {
                    **context,
                    'participant': participant,
                })
                plain_message = render_to_string('video_chat/emails/session_cancelled.txt', {
                    **context,
                    'participant': participant,
                })
                
                # Send email
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[participant.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                logger.info(f"Sent session cancelled notification to {participant.email}")
                
            except Exception as e:
                logger.error(f"Error sending notification to {participant.email}: {str(e)}")
    
    @staticmethod
    def send_session_updated_notification(session):
        """
        Send notification when a session is updated (rescheduled).
        Requirements: 5.2
        
        Args:
            session: VideoSession instance
        """
        # Get all invited participants
        participant_records = VideoSessionParticipant.objects.filter(
            session=session,
            status='invited'
        ).exclude(user=session.host).select_related('user')
        
        if not participant_records:
            return
        
        # Generate session URL
        session_url = f"{settings.SITE_URL}{reverse('video_chat:session_detail', kwargs={'session_id': session.session_id})}"
        
        # Prepare email context
        context = {
            'session': session,
            'session_url': session_url,
            'host': session.host,
        }
        
        # Send notification to each participant
        for participant_record in participant_records:
            participant = participant_record.user
            
            try:
                # Render email content
                subject = f"Video Session Updated: {session.title}"
                html_message = render_to_string('video_chat/emails/session_updated.html', {
                    **context,
                    'participant': participant,
                })
                plain_message = render_to_string('video_chat/emails/session_updated.txt', {
                    **context,
                    'participant': participant,
                })
                
                # Send email
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[participant.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                logger.info(f"Sent session updated notification to {participant.email}")
                
            except Exception as e:
                logger.error(f"Error sending notification to {participant.email}: {str(e)}")
    
    @staticmethod
    def can_join_early(session):
        """
        Check if participants can join early (10 minutes before scheduled time).
        Requirements: 5.5
        
        Args:
            session: VideoSession instance
            
        Returns:
            bool: True if early join is allowed
        """
        if not session.scheduled_time:
            return True  # No scheduled time, can join anytime
        
        if session.status == 'active':
            return True  # Session is already active
        
        if session.status != 'scheduled':
            return False  # Can't join cancelled or completed sessions
        
        now = timezone.now()
        early_join_time = session.scheduled_time - timedelta(minutes=10)
        
        return now >= early_join_time
    
    @staticmethod
    def get_time_until_early_join(session):
        """
        Get the time remaining until early join is available.
        Requirements: 5.5
        
        Args:
            session: VideoSession instance
            
        Returns:
            timedelta or None: Time remaining until early join, or None if can join now
        """
        if not session.scheduled_time or session.status != 'scheduled':
            return None
        
        now = timezone.now()
        early_join_time = session.scheduled_time - timedelta(minutes=10)
        
        if now >= early_join_time:
            return None  # Can join now
        
        return early_join_time - now
    
    @staticmethod
    def generate_calendar_entry(session):
        """
        Generate iCalendar (.ics) format for the session.
        Requirements: 5.2
        
        Args:
            session: VideoSession instance
            
        Returns:
            str: iCalendar formatted string
        """
        if not session.scheduled_time:
            return None
        
        # Calculate end time
        end_time = session.scheduled_time + timedelta(minutes=session.duration_minutes)
        
        # Generate join URL
        join_url = f"{settings.SITE_URL}{reverse('video_chat:join_session', kwargs={'session_id': session.session_id})}"
        
        # Format times for iCalendar (UTC, format: YYYYMMDDTHHmmssZ)
        start_utc = session.scheduled_time.astimezone(timezone.utc)
        end_utc = end_time.astimezone(timezone.utc)
        
        start_str = start_utc.strftime('%Y%m%dT%H%M%SZ')
        end_str = end_utc.strftime('%Y%m%dT%H%M%SZ')
        created_str = session.created_at.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        
        # Build iCalendar content
        ical = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//MetLab Education//Video Chat//EN
CALSCALE:GREGORIAN
METHOD:REQUEST
BEGIN:VEVENT
UID:{session.session_id}@metlab.edu
DTSTAMP:{created_str}
DTSTART:{start_str}
DTEND:{end_str}
SUMMARY:{session.title}
DESCRIPTION:{session.description}\\n\\nJoin URL: {join_url}
LOCATION:{join_url}
ORGANIZER;CN={session.host.get_full_name() or session.host.username}:mailto:{session.host.email}
STATUS:CONFIRMED
SEQUENCE:0
BEGIN:VALARM
TRIGGER:-PT15M
ACTION:DISPLAY
DESCRIPTION:Video session starting in 15 minutes
END:VALARM
END:VEVENT
END:VCALENDAR"""
        
        return ical
    
    @staticmethod
    def get_sessions_needing_reminders():
        """
        Get sessions that need reminder notifications (15 minutes before start).
        Requirements: 5.3
        
        Returns:
            QuerySet: VideoSession objects needing reminders
        """
        now = timezone.now()
        reminder_time = now + timedelta(minutes=15)
        
        # Get scheduled sessions starting in approximately 15 minutes
        # Use a 2-minute window to account for task execution delays
        sessions = VideoSession.objects.filter(
            status='scheduled',
            scheduled_time__gte=now + timedelta(minutes=13),
            scheduled_time__lte=now + timedelta(minutes=17)
        )
        
        return sessions
