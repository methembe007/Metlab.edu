"""
Management command to send reminder notifications for upcoming video sessions.
This should be run periodically (e.g., every 5 minutes via cron or task scheduler).
Requirements: 5.3
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from video_chat.notifications import VideoSessionNotificationService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send reminder notifications for video sessions starting in 15 minutes'
    
    def handle(self, *args, **options):
        """Send reminders for upcoming sessions"""
        self.stdout.write('Checking for sessions needing reminders...')
        
        # Get sessions that need reminders
        sessions = VideoSessionNotificationService.get_sessions_needing_reminders()
        
        if not sessions.exists():
            self.stdout.write(self.style.SUCCESS('No sessions need reminders at this time'))
            return
        
        self.stdout.write(f'Found {sessions.count()} session(s) needing reminders')
        
        # Send reminders for each session
        for session in sessions:
            try:
                self.stdout.write(f'Sending reminder for session: {session.title}')
                VideoSessionNotificationService.send_session_reminder(session)
                self.stdout.write(self.style.SUCCESS(f'✓ Sent reminder for: {session.title}'))
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error sending reminder for {session.title}: {str(e)}')
                )
                logger.error(f'Error sending reminder for session {session.session_id}: {str(e)}')
        
        self.stdout.write(self.style.SUCCESS('Reminder check complete'))
