"""
Service layer for video chat session management.
Handles business logic for session lifecycle, participant management, and event logging.
"""
import logging
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from .models import VideoSession, VideoSessionParticipant, VideoSessionEvent

logger = logging.getLogger(__name__)


class VideoSessionService:
    """Service class for managing video session lifecycle and operations"""
    
    @staticmethod
    def create_session(host, session_type, title, description='', 
                      scheduled_time=None, duration_minutes=60,
                      max_participants=30, allow_screen_share=True,
                      require_approval=False, teacher_class=None, 
                      tutor_booking=None, **kwargs):
        """
        Create a new video session.
        
        Args:
            host: User object who is hosting the session
            session_type: Type of session ('one_on_one', 'group', 'class')
            title: Session title
            description: Optional session description
            scheduled_time: DateTime for scheduled sessions (None for immediate)
            duration_minutes: Expected session duration
            max_participants: Maximum number of participants allowed
            allow_screen_share: Whether screen sharing is enabled
            require_approval: Whether participants need approval to join
            teacher_class: Optional TeacherClass instance for class sessions
            tutor_booking: Optional TutorBooking instance for tutoring sessions
            
        Returns:
            VideoSession instance
            
        Raises:
            ValidationError: If validation fails
            PermissionDenied: If user doesn't have permission to create session
        """
        from .permissions import VideoSessionPermissions
        from .rate_limiting import VideoSessionRateLimiter, SessionAbuseDetector
        
        # Validate session type
        valid_types = ['one_on_one', 'group', 'class']
        if session_type not in valid_types:
            raise ValidationError(f"Invalid session type. Must be one of: {valid_types}")
        
        # Validate host permissions
        if not host.is_authenticated:
            raise PermissionDenied("User must be authenticated to create a session")
        
        # Check rate limiting for session creation
        is_allowed, remaining, reset_time = VideoSessionRateLimiter.check_session_creation_limit(host)
        if not is_allowed:
            reset_msg = f" Try again in {reset_time.strftime('%H:%M:%S')}" if reset_time else ""
            raise ValidationError(
                f"Session creation rate limit exceeded. "
                f"Maximum {VideoSessionRateLimiter.SESSION_CREATION_LIMIT} sessions per hour.{reset_msg}"
            )
        
        # Check for abuse patterns
        if SessionAbuseDetector.track_rapid_session_creation(host):
            logger.warning(f"Rapid session creation detected for user {host.username}")
            # Flag user if pattern is very suspicious
            SessionAbuseDetector.flag_user(
                host,
                "Rapid session creation pattern detected",
                duration_hours=1
            )
        
        # Check if user is flagged for abuse
        is_flagged, flag_reason = SessionAbuseDetector.is_user_flagged(host)
        if is_flagged:
            raise PermissionDenied(f"Session creation temporarily restricted: {flag_reason}")
        
        # Check if user can create this type of session
        can_create, reason = VideoSessionPermissions.can_user_create_session(
            host, session_type, teacher_class, tutor_booking
        )
        if not can_create:
            raise PermissionDenied(reason)
        
        # Validate one-on-one session has max 2 participants
        if session_type == 'one_on_one' and max_participants > 2:
            max_participants = 2
        
        # Validate session size based on SFU availability
        from .sfu_config import SFUConfig
        is_valid, error_message = SFUConfig.validate_session_size(session_type, max_participants)
        if not is_valid:
            raise ValidationError(error_message)
        
        # Determine initial status
        if scheduled_time and scheduled_time > timezone.now():
            status = 'scheduled'
        else:
            status = 'scheduled'  # Will be set to 'active' when started
        
        with transaction.atomic():
            # Create the session
            session = VideoSession.objects.create(
                session_type=session_type,
                host=host,
                title=title,
                description=description,
                scheduled_time=scheduled_time,
                duration_minutes=duration_minutes,
                status=status,
                max_participants=max_participants,
                allow_screen_share=allow_screen_share,
                require_approval=require_approval,
                teacher_class=teacher_class,
                tutor_booking=tutor_booking,
                **kwargs
            )
            
            # Add host as a participant with 'host' role
            VideoSessionParticipant.objects.create(
                session=session,
                user=host,
                role='host',
                status='invited'
            )
            
            # Log session creation event
            VideoSessionEvent.objects.create(
                session=session,
                event_type='session_started',
                user=host,
                details={
                    'action': 'session_created',
                    'session_type': session_type,
                    'scheduled': scheduled_time is not None
                }
            )
        
        return session
    
    @staticmethod
    def schedule_session(session_id, scheduled_time, user=None):
        """
        Schedule or reschedule a video session.
        
        Args:
            session_id: UUID of the session
            scheduled_time: DateTime for the scheduled session
            user: Optional user performing the action (for logging)
            
        Returns:
            Updated VideoSession instance
            
        Raises:
            VideoSession.DoesNotExist: If session not found
            ValidationError: If validation fails
        """
        try:
            session = VideoSession.objects.get(session_id=session_id)
        except VideoSession.DoesNotExist:
            raise VideoSession.DoesNotExist(f"Session with ID {session_id} not found")
        
        # Validate session can be scheduled
        if session.status == 'active':
            raise ValidationError("Cannot reschedule an active session")
        
        if session.status == 'completed':
            raise ValidationError("Cannot reschedule a completed session")
        
        # Validate scheduled time is in the future
        if scheduled_time <= timezone.now():
            raise ValidationError("Scheduled time must be in the future")
        
        with transaction.atomic():
            # Update session
            old_time = session.scheduled_time
            session.scheduled_time = scheduled_time
            session.status = 'scheduled'
            session.save(update_fields=['scheduled_time', 'status', 'updated_at'])
            
            # Log scheduling event
            VideoSessionEvent.objects.create(
                session=session,
                event_type='session_started',
                user=user or session.host,
                details={
                    'action': 'session_scheduled',
                    'old_time': old_time.isoformat() if old_time else None,
                    'new_time': scheduled_time.isoformat()
                }
            )
        
        return session
    
    @staticmethod
    def start_session(session_id, user):
        """
        Start a video session.
        
        Args:
            session_id: UUID of the session
            user: User starting the session (must be host)
            
        Returns:
            Updated VideoSession instance
            
        Raises:
            VideoSession.DoesNotExist: If session not found
            PermissionDenied: If user is not the host
            ValidationError: If session cannot be started
        """
        try:
            session = VideoSession.objects.get(session_id=session_id)
        except VideoSession.DoesNotExist:
            raise VideoSession.DoesNotExist(f"Session with ID {session_id} not found")
        
        # Verify user is the host
        if session.host != user:
            raise PermissionDenied("Only the session host can start the session")
        
        # Validate session status
        if session.status == 'active':
            raise ValidationError("Session is already active")
        
        if session.status == 'completed':
            raise ValidationError("Cannot start a completed session")
        
        if session.status == 'cancelled':
            raise ValidationError("Cannot start a cancelled session")
        
        with transaction.atomic():
            # Update session status
            session.status = 'active'
            session.started_at = timezone.now()
            session.save(update_fields=['status', 'started_at', 'updated_at'])
            
            # Log session start event
            VideoSessionEvent.objects.create(
                session=session,
                event_type='session_started',
                user=user,
                details={
                    'action': 'session_started',
                    'started_at': session.started_at.isoformat()
                }
            )
        
        return session
    
    @staticmethod
    def end_session(session_id, user):
        """
        End a video session.
        
        Args:
            session_id: UUID of the session
            user: User ending the session (must be host)
            
        Returns:
            Updated VideoSession instance
            
        Raises:
            VideoSession.DoesNotExist: If session not found
            PermissionDenied: If user is not the host
            ValidationError: If session cannot be ended
        """
        try:
            session = VideoSession.objects.get(session_id=session_id)
        except VideoSession.DoesNotExist:
            raise VideoSession.DoesNotExist(f"Session with ID {session_id} not found")
        
        # Verify user is the host
        if session.host != user:
            raise PermissionDenied("Only the session host can end the session")
        
        # Validate session status
        if session.status != 'active':
            raise ValidationError("Only active sessions can be ended")
        
        with transaction.atomic():
            # Update session status
            session.status = 'completed'
            session.ended_at = timezone.now()
            session.save(update_fields=['status', 'ended_at', 'updated_at'])
            
            # Update all joined participants to 'left' status
            active_participants = session.participants.filter(status='joined')
            for participant in active_participants:
                participant.status = 'left'
                participant.left_at = timezone.now()
                participant.save(update_fields=['status', 'left_at', 'updated_at'])
            
            # Update tutor booking status if this is a tutoring session
            if session.tutor_booking:
                session.tutor_booking.status = 'completed'
                session.tutor_booking.save(update_fields=['status', 'updated_at'])
            
            # Log session end event
            VideoSessionEvent.objects.create(
                session=session,
                event_type='session_ended',
                user=user,
                details={
                    'action': 'session_ended',
                    'ended_at': session.ended_at.isoformat(),
                    'duration_seconds': (session.ended_at - session.started_at).total_seconds() if session.started_at else 0,
                    'participant_count': session.participants.count()
                }
            )
        
        return session
    
    @staticmethod
    def cancel_session(session_id, user, reason=''):
        """
        Cancel a scheduled video session.
        
        Args:
            session_id: UUID of the session
            user: User cancelling the session (must be host)
            reason: Optional cancellation reason
            
        Returns:
            Updated VideoSession instance
            
        Raises:
            VideoSession.DoesNotExist: If session not found
            PermissionDenied: If user is not the host
            ValidationError: If session cannot be cancelled
        """
        try:
            session = VideoSession.objects.get(session_id=session_id)
        except VideoSession.DoesNotExist:
            raise VideoSession.DoesNotExist(f"Session with ID {session_id} not found")
        
        # Verify user is the host
        if session.host != user:
            raise PermissionDenied("Only the session host can cancel the session")
        
        # Validate session status
        if session.status == 'completed':
            raise ValidationError("Cannot cancel a completed session")
        
        if session.status == 'cancelled':
            raise ValidationError("Session is already cancelled")
        
        if session.status == 'active':
            raise ValidationError("Cannot cancel an active session. End it instead.")
        
        with transaction.atomic():
            # Update session status
            session.status = 'cancelled'
            session.save(update_fields=['status', 'updated_at'])
            
            # Update all invited participants to 'removed' status
            invited_participants = session.participants.filter(status='invited')
            invited_participants.update(status='removed', updated_at=timezone.now())
            
            # Log cancellation event
            VideoSessionEvent.objects.create(
                session=session,
                event_type='session_ended',
                user=user,
                details={
                    'action': 'session_cancelled',
                    'reason': reason,
                    'cancelled_at': timezone.now().isoformat()
                }
            )
        
        return session
    
    @staticmethod
    def get_session(session_id):
        """
        Retrieve a video session by ID.
        
        Args:
            session_id: UUID of the session
            
        Returns:
            VideoSession instance
            
        Raises:
            VideoSession.DoesNotExist: If session not found
        """
        try:
            return VideoSession.objects.select_related(
                'host', 'teacher_class', 'tutor_booking'
            ).prefetch_related('participants__user').get(session_id=session_id)
        except VideoSession.DoesNotExist:
            raise VideoSession.DoesNotExist(f"Session with ID {session_id} not found")
    
    @staticmethod
    def get_user_sessions(user, status=None, include_as_participant=True):
        """
        Get all sessions for a user.
        
        Args:
            user: User object
            status: Optional status filter ('scheduled', 'active', 'completed', 'cancelled')
            include_as_participant: Whether to include sessions where user is a participant
            
        Returns:
            QuerySet of VideoSession objects
        """
        # Get sessions where user is host
        sessions = VideoSession.objects.filter(host=user)
        
        # Include sessions where user is a participant
        if include_as_participant:
            participant_sessions = VideoSession.objects.filter(
                participants__user=user
            ).exclude(host=user)
            sessions = sessions | participant_sessions
        
        # Filter by status if provided
        if status:
            sessions = sessions.filter(status=status)
        
        return sessions.select_related(
            'host', 'teacher_class', 'tutor_booking'
        ).prefetch_related('participants__user').distinct().order_by('-created_at')
    
    @staticmethod
    def join_session(session_id, user):
        """
        Add a participant to a video session.
        
        Args:
            session_id: UUID of the session
            user: User joining the session
            
        Returns:
            VideoSessionParticipant instance
            
        Raises:
            VideoSession.DoesNotExist: If session not found
            ValidationError: If user cannot join the session
            PermissionDenied: If user doesn't have permission to join
        """
        from .permissions import VideoSessionPermissions
        from .rate_limiting import VideoSessionRateLimiter, SessionAbuseDetector
        
        try:
            session = VideoSession.objects.select_related('host').get(session_id=session_id)
        except VideoSession.DoesNotExist:
            raise VideoSession.DoesNotExist(f"Session with ID {session_id} not found")
        
        # Check rate limiting for join attempts
        is_allowed, remaining, reset_time = VideoSessionRateLimiter.check_join_attempt_limit(user, session_id)
        if not is_allowed:
            reset_msg = f" Try again in {reset_time.strftime('%H:%M:%S')}" if reset_time else ""
            raise ValidationError(
                f"Join attempt rate limit exceeded. "
                f"Maximum {VideoSessionRateLimiter.JOIN_ATTEMPT_LIMIT} attempts per 5 minutes.{reset_msg}"
            )
        
        # Check if user is flagged for abuse
        is_flagged, flag_reason = SessionAbuseDetector.is_user_flagged(user)
        if is_flagged:
            raise PermissionDenied(f"Session access temporarily restricted: {flag_reason}")
        
        # Check if user has permission to join this session
        can_join, reason = VideoSessionPermissions.can_user_join_session(user, session)
        if not can_join:
            raise PermissionDenied(reason)
        
        # Check if user is already in another active session (busy status)
        active_participant = VideoSessionParticipant.objects.filter(
            user=user,
            status='joined',
            session__status='active'
        ).exclude(session=session).first()
        
        if active_participant:
            raise ValidationError(
                f"User is already in an active session: {active_participant.session.title}"
            )
        
        # Validate session status
        if session.status == 'completed':
            raise ValidationError("Cannot join a completed session")
        
        if session.status == 'cancelled':
            raise ValidationError("Cannot join a cancelled session")
        
        with transaction.atomic():
            # Get or create participant record
            participant, created = VideoSessionParticipant.objects.get_or_create(
                session=session,
                user=user,
                defaults={
                    'role': 'host' if user == session.host else 'participant',
                    'status': 'invited'
                }
            )
            
            # Check participant limit (excluding current user if already a participant)
            current_participant_count = session.participants.filter(
                status__in=['invited', 'joined']
            ).exclude(user=user).count()
            
            # If this is a new participant, check if there's room
            if created and current_participant_count >= session.max_participants:
                # Delete the just-created participant record
                participant.delete()
                raise ValidationError(
                    f"Session has reached maximum capacity ({session.max_participants} participants)"
                )
            
            # If participant already exists but left, allow rejoin
            if not created and participant.status == 'left':
                participant.status = 'joined'
                participant.joined_at = timezone.now()
                participant.left_at = None
                participant.save(update_fields=['status', 'joined_at', 'left_at', 'updated_at'])
            elif not created and participant.status == 'joined':
                # Already joined
                return participant
            elif not created and participant.status == 'removed':
                raise PermissionDenied("You have been removed from this session")
            else:
                # New participant or invited participant joining
                participant.status = 'joined'
                participant.joined_at = timezone.now()
                participant.save(update_fields=['status', 'joined_at', 'updated_at'])
            
            # Log participant joined event
            VideoSessionEvent.objects.create(
                session=session,
                event_type='participant_joined',
                user=user,
                details={
                    'action': 'participant_joined',
                    'participant_id': participant.id,
                    'joined_at': participant.joined_at.isoformat(),
                    'participant_count': session.participants.filter(status='joined').count()
                }
            )
            
            # Send notification to parents if user is a student
            try:
                from accounts.models import StudentProfile
                student_profile = StudentProfile.objects.filter(user=user).first()
                if student_profile:
                    # Notify all linked parents
                    for parent in student_profile.parents.all():
                        # Log notification (actual email/push notification would be sent here)
                        logger.info(
                            f"Parent notification: {student_profile.user.get_full_name() or student_profile.user.username} "
                            f"joined video session '{session.title}' at {participant.joined_at}"
                        )
            except Exception as e:
                logger.error(f"Error sending parent notification for join: {str(e)}")
        
        return participant
    
    @staticmethod
    def leave_session(session_id, user):
        """
        Remove a participant from a video session.
        
        Args:
            session_id: UUID of the session
            user: User leaving the session
            
        Returns:
            Updated VideoSessionParticipant instance
            
        Raises:
            VideoSession.DoesNotExist: If session not found
            VideoSessionParticipant.DoesNotExist: If user is not a participant
            ValidationError: If user cannot leave the session
        """
        try:
            session = VideoSession.objects.get(session_id=session_id)
        except VideoSession.DoesNotExist:
            raise VideoSession.DoesNotExist(f"Session with ID {session_id} not found")
        
        try:
            participant = VideoSessionParticipant.objects.get(
                session=session,
                user=user
            )
        except VideoSessionParticipant.DoesNotExist:
            raise VideoSessionParticipant.DoesNotExist(
                f"User {user.username} is not a participant in this session"
            )
        
        # Validate participant status
        if participant.status != 'joined':
            raise ValidationError(f"Participant is not currently joined (status: {participant.status})")
        
        with transaction.atomic():
            # Update participant status
            participant.status = 'left'
            participant.left_at = timezone.now()
            participant.audio_enabled = False
            participant.video_enabled = False
            participant.screen_sharing = False
            participant.save(update_fields=[
                'status', 'left_at', 'audio_enabled', 
                'video_enabled', 'screen_sharing', 'updated_at'
            ])
            
            # Log participant left event
            VideoSessionEvent.objects.create(
                session=session,
                event_type='participant_left',
                user=user,
                details={
                    'action': 'participant_left',
                    'participant_id': participant.id,
                    'left_at': participant.left_at.isoformat(),
                    'duration_seconds': (participant.left_at - participant.joined_at).total_seconds() if participant.joined_at else 0,
                    'remaining_participants': session.participants.filter(status='joined').count()
                }
            )
            
            # Send notification to parents if user is a student
            try:
                from accounts.models import StudentProfile
                student_profile = StudentProfile.objects.filter(user=user).first()
                if student_profile:
                    # Calculate session duration
                    duration_minutes = int((participant.left_at - participant.joined_at).total_seconds() / 60) if participant.joined_at else 0
                    
                    # Notify all linked parents
                    for parent in student_profile.parents.all():
                        # Log notification (actual email/push notification would be sent here)
                        logger.info(
                            f"Parent notification: {student_profile.user.get_full_name() or student_profile.user.username} "
                            f"left video session '{session.title}' at {participant.left_at}. Duration: {duration_minutes} minutes"
                        )
            except Exception as e:
                logger.error(f"Error sending parent notification for leave: {str(e)}")
        
        return participant
    
    @staticmethod
    def remove_participant(session_id, user_to_remove, removed_by):
        """
        Remove a participant from a session (host action).
        
        Args:
            session_id: UUID of the session
            user_to_remove: User to be removed from the session
            removed_by: User performing the removal (must be host)
            
        Returns:
            Updated VideoSessionParticipant instance
            
        Raises:
            VideoSession.DoesNotExist: If session not found
            VideoSessionParticipant.DoesNotExist: If user is not a participant
            PermissionDenied: If removed_by is not the host
            ValidationError: If removal is not allowed
        """
        try:
            session = VideoSession.objects.select_related('host').get(session_id=session_id)
        except VideoSession.DoesNotExist:
            raise VideoSession.DoesNotExist(f"Session with ID {session_id} not found")
        
        # Verify removed_by is the host
        if session.host != removed_by:
            raise PermissionDenied("Only the session host can remove participants")
        
        # Cannot remove the host
        if user_to_remove == session.host:
            raise ValidationError("Cannot remove the session host")
        
        try:
            participant = VideoSessionParticipant.objects.get(
                session=session,
                user=user_to_remove
            )
        except VideoSessionParticipant.DoesNotExist:
            raise VideoSessionParticipant.DoesNotExist(
                f"User {user_to_remove.username} is not a participant in this session"
            )
        
        with transaction.atomic():
            # Update participant status
            old_status = participant.status
            participant.status = 'removed'
            
            if old_status == 'joined':
                participant.left_at = timezone.now()
            
            participant.audio_enabled = False
            participant.video_enabled = False
            participant.screen_sharing = False
            participant.save(update_fields=[
                'status', 'left_at', 'audio_enabled',
                'video_enabled', 'screen_sharing', 'updated_at'
            ])
            
            # Log participant removal event
            VideoSessionEvent.objects.create(
                session=session,
                event_type='participant_left',
                user=removed_by,
                details={
                    'action': 'participant_removed',
                    'removed_user_id': user_to_remove.id,
                    'removed_username': user_to_remove.username,
                    'removed_by': removed_by.username,
                    'removed_at': timezone.now().isoformat(),
                    'previous_status': old_status
                }
            )
        
        return participant
    
    @staticmethod
    def get_session_participants(session_id, status_filter=None):
        """
        Get all participants in a session.
        
        Args:
            session_id: UUID of the session
            status_filter: Optional status filter ('invited', 'joined', 'left', 'removed')
            
        Returns:
            QuerySet of VideoSessionParticipant objects
            
        Raises:
            VideoSession.DoesNotExist: If session not found
        """
        try:
            session = VideoSession.objects.get(session_id=session_id)
        except VideoSession.DoesNotExist:
            raise VideoSession.DoesNotExist(f"Session with ID {session_id} not found")
        
        participants = session.participants.select_related('user').all()
        
        if status_filter:
            participants = participants.filter(status=status_filter)
        
        return participants.order_by('joined_at')
    
    @staticmethod
    def is_user_busy(user):
        """
        Check if a user is currently in an active video session.
        
        Args:
            user: User object to check
            
        Returns:
            Tuple of (is_busy: bool, active_session: VideoSession or None)
        """
        active_participant = VideoSessionParticipant.objects.filter(
            user=user,
            status='joined',
            session__status='active'
        ).select_related('session').first()
        
        if active_participant:
            return True, active_participant.session
        
        return False, None
    
    @staticmethod
    def update_participant_media_state(session_id, user, audio_enabled=None, 
                                      video_enabled=None, screen_sharing=None):
        """
        Update a participant's media state (audio/video/screen sharing).
        
        Args:
            session_id: UUID of the session
            user: User whose media state is being updated
            audio_enabled: Optional boolean for audio state
            video_enabled: Optional boolean for video state
            screen_sharing: Optional boolean for screen sharing state
            
        Returns:
            Updated VideoSessionParticipant instance
            
        Raises:
            VideoSession.DoesNotExist: If session not found
            VideoSessionParticipant.DoesNotExist: If user is not a participant
        """
        try:
            session = VideoSession.objects.get(session_id=session_id)
        except VideoSession.DoesNotExist:
            raise VideoSession.DoesNotExist(f"Session with ID {session_id} not found")
        
        try:
            participant = VideoSessionParticipant.objects.get(
                session=session,
                user=user,
                status='joined'
            )
        except VideoSessionParticipant.DoesNotExist:
            raise VideoSessionParticipant.DoesNotExist(
                f"User {user.username} is not an active participant in this session"
            )
        
        # Update fields that were provided
        update_fields = ['updated_at']
        
        if audio_enabled is not None:
            participant.audio_enabled = audio_enabled
            update_fields.append('audio_enabled')
        
        if video_enabled is not None:
            participant.video_enabled = video_enabled
            update_fields.append('video_enabled')
        
        if screen_sharing is not None:
            participant.screen_sharing = screen_sharing
            update_fields.append('screen_sharing')
            
            # Log screen sharing events
            if screen_sharing:
                VideoSessionEvent.objects.create(
                    session=session,
                    event_type='screen_share_started',
                    user=user,
                    details={
                        'action': 'screen_share_started',
                        'participant_id': participant.id
                    }
                )
            else:
                VideoSessionEvent.objects.create(
                    session=session,
                    event_type='screen_share_stopped',
                    user=user,
                    details={
                        'action': 'screen_share_stopped',
                        'participant_id': participant.id
                    }
                )
        
        participant.save(update_fields=update_fields)
        
        return participant
    
    @staticmethod
    def get_session_history(user, start_date=None, end_date=None, limit=None):
        """
        Retrieve session history for a user.
        
        Args:
            user: User object to get history for
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Optional limit on number of results
            
        Returns:
            QuerySet of VideoSession objects with related data
        """
        # Get sessions where user is host or participant
        sessions = VideoSession.objects.filter(
            participants__user=user
        ).select_related(
            'host', 'teacher_class', 'tutor_booking'
        ).prefetch_related(
            'participants__user', 'events'
        ).distinct()
        
        # Filter by date range if provided
        if start_date:
            sessions = sessions.filter(created_at__gte=start_date)
        
        if end_date:
            sessions = sessions.filter(created_at__lte=end_date)
        
        # Order by most recent first
        sessions = sessions.order_by('-created_at')
        
        # Apply limit if provided
        if limit:
            sessions = sessions[:limit]
        
        return sessions
    
    @staticmethod
    def get_session_events(session_id, event_type=None):
        """
        Retrieve all events for a specific session.
        
        Args:
            session_id: UUID of the session
            event_type: Optional filter for specific event type
            
        Returns:
            QuerySet of VideoSessionEvent objects
            
        Raises:
            VideoSession.DoesNotExist: If session not found
        """
        try:
            session = VideoSession.objects.get(session_id=session_id)
        except VideoSession.DoesNotExist:
            raise VideoSession.DoesNotExist(f"Session with ID {session_id} not found")
        
        events = session.events.select_related('user').all()
        
        if event_type:
            events = events.filter(event_type=event_type)
        
        return events.order_by('timestamp')
    
    @staticmethod
    def get_parent_monitoring_data(parent_user, child_user=None, start_date=None, end_date=None):
        """
        Retrieve video session monitoring data for parents.
        
        Args:
            parent_user: Parent User object
            child_user: Optional specific child User object to filter by
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dictionary containing session history and statistics
            
        Raises:
            PermissionDenied: If parent_user doesn't have parent profile
        """
        from accounts.models import ParentProfile
        
        # Verify user has parent profile
        try:
            parent_profile = ParentProfile.objects.get(user=parent_user)
        except ParentProfile.DoesNotExist:
            raise PermissionDenied("User does not have a parent profile")
        
        # Get linked children (StudentProfile objects)
        linked_student_profiles = parent_profile.children.all()
        
        if not linked_student_profiles.exists():
            return {
                'sessions': [],
                'statistics': {
                    'total_sessions': 0,
                    'total_duration_minutes': 0,
                    'sessions_by_type': {},
                    'unique_teachers': set(),
                    'recent_activity': []
                },
                'children': []
            }
        
        # Get User objects from StudentProfile objects
        linked_children = [profile.user for profile in linked_student_profiles]
        
        # Filter by specific child if provided
        if child_user:
            if child_user not in linked_children:
                raise PermissionDenied("Specified child is not linked to this parent")
            children_to_monitor = [child_user]
        else:
            children_to_monitor = linked_children
        
        # Get all sessions for the children
        sessions_query = VideoSession.objects.filter(
            participants__user__in=children_to_monitor
        ).select_related(
            'host', 'teacher_class', 'tutor_booking'
        ).prefetch_related(
            'participants__user', 'events'
        ).distinct()
        
        # Apply date filters
        if start_date:
            sessions_query = sessions_query.filter(created_at__gte=start_date)
        
        if end_date:
            sessions_query = sessions_query.filter(created_at__lte=end_date)
        
        sessions = sessions_query.order_by('-created_at')
        
        # Calculate statistics
        total_sessions = sessions.count()
        total_duration_minutes = 0
        sessions_by_type = {}
        unique_teachers = set()
        
        for session in sessions:
            # Calculate duration
            if session.started_at and session.ended_at:
                duration = (session.ended_at - session.started_at).total_seconds() / 60
                total_duration_minutes += duration
            
            # Count by type
            sessions_by_type[session.session_type] = sessions_by_type.get(session.session_type, 0) + 1
            
            # Track unique teachers
            if session.host.id not in [child.id for child in children_to_monitor]:
                unique_teachers.add(session.host.username)
        
        # Get recent activity (last 10 events)
        recent_events = VideoSessionEvent.objects.filter(
            session__in=sessions,
            user__in=children_to_monitor
        ).select_related('session', 'user').order_by('-timestamp')[:10]
        
        recent_activity = [
            {
                'event_type': event.event_type,
                'session_title': event.session.title,
                'child_username': event.user.username if event.user else None,
                'timestamp': event.timestamp,
                'details': event.details
            }
            for event in recent_events
        ]
        
        # Build detailed session list with child participation info
        session_details = []
        for session in sessions:
            # Get child participants in this session
            child_participants = session.participants.filter(
                user__in=children_to_monitor
            ).select_related('user')
            
            session_info = {
                'session_id': str(session.session_id),
                'title': session.title,
                'session_type': session.session_type,
                'host': session.host.username,
                'status': session.status,
                'scheduled_time': session.scheduled_time,
                'started_at': session.started_at,
                'ended_at': session.ended_at,
                'duration_minutes': (session.ended_at - session.started_at).total_seconds() / 60 if session.started_at and session.ended_at else None,
                'child_participants': [
                    {
                        'username': p.user.username,
                        'joined_at': p.joined_at,
                        'left_at': p.left_at,
                        'duration_minutes': (p.left_at - p.joined_at).total_seconds() / 60 if p.joined_at and p.left_at else None,
                        'status': p.status
                    }
                    for p in child_participants
                ],
                'total_participants': session.participants.count(),
                'is_recorded': session.is_recorded,
                'recording_url': session.recording_url if session.is_recorded else None
            }
            session_details.append(session_info)
        
        return {
            'sessions': session_details,
            'statistics': {
                'total_sessions': total_sessions,
                'total_duration_minutes': round(total_duration_minutes, 2),
                'sessions_by_type': sessions_by_type,
                'unique_teachers': list(unique_teachers),
                'recent_activity': recent_activity
            },
            'children': [
                {
                    'id': child.id,
                    'username': child.username,
                    'full_name': child.get_full_name()
                }
                for child in children_to_monitor
            ]
        }
    
    @staticmethod
    def get_child_session_summary(child_user, start_date=None, end_date=None):
        """
        Get a summary of video sessions for a specific child.
        
        Args:
            child_user: Child User object
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dictionary containing session summary and statistics
        """
        # Get all sessions for the child
        sessions = VideoSession.objects.filter(
            participants__user=child_user
        ).select_related('host').prefetch_related('participants')
        
        # Apply date filters
        if start_date:
            sessions = sessions.filter(created_at__gte=start_date)
        
        if end_date:
            sessions = sessions.filter(created_at__lte=end_date)
        
        sessions = sessions.distinct()
        
        # Calculate statistics
        total_sessions = sessions.count()
        completed_sessions = sessions.filter(status='completed').count()
        total_duration_minutes = 0
        sessions_by_type = {}
        teachers_interacted = set()
        
        for session in sessions:
            # Calculate duration for completed sessions
            if session.status == 'completed' and session.started_at and session.ended_at:
                duration = (session.ended_at - session.started_at).total_seconds() / 60
                total_duration_minutes += duration
            
            # Count by type
            sessions_by_type[session.session_type] = sessions_by_type.get(session.session_type, 0) + 1
            
            # Track teachers
            if session.host != child_user:
                teachers_interacted.add(session.host.username)
        
        # Get participation details
        participations = VideoSessionParticipant.objects.filter(
            user=child_user,
            session__in=sessions
        ).select_related('session')
        
        total_time_in_sessions = 0
        for participation in participations:
            if participation.joined_at and participation.left_at:
                duration = (participation.left_at - participation.joined_at).total_seconds() / 60
                total_time_in_sessions += duration
        
        return {
            'total_sessions': total_sessions,
            'completed_sessions': completed_sessions,
            'total_duration_minutes': round(total_duration_minutes, 2),
            'total_participation_minutes': round(total_time_in_sessions, 2),
            'sessions_by_type': sessions_by_type,
            'teachers_interacted': list(teachers_interacted),
            'average_session_duration': round(total_duration_minutes / completed_sessions, 2) if completed_sessions > 0 else 0
        }
    
    @staticmethod
    def log_event(session_id, event_type, user=None, details=None):
        """
        Log a custom event for a video session.
        
        Args:
            session_id: UUID of the session
            event_type: Type of event (must be valid choice)
            user: Optional User object associated with the event
            details: Optional dictionary of additional event details
            
        Returns:
            VideoSessionEvent instance
            
        Raises:
            VideoSession.DoesNotExist: If session not found
            ValidationError: If event_type is invalid
        """
        try:
            session = VideoSession.objects.get(session_id=session_id)
        except VideoSession.DoesNotExist:
            raise VideoSession.DoesNotExist(f"Session with ID {session_id} not found")
        
        # Validate event type
        valid_event_types = [choice[0] for choice in VideoSessionEvent.EVENT_TYPE_CHOICES]
        if event_type not in valid_event_types:
            raise ValidationError(f"Invalid event type. Must be one of: {valid_event_types}")
        
        event = VideoSessionEvent.objects.create(
            session=session,
            event_type=event_type,
            user=user,
            details=details or {}
        )
        
        return event
    
    @staticmethod
    def get_session_statistics(session_id):
        """
        Get detailed statistics for a specific session.
        
        Args:
            session_id: UUID of the session
            
        Returns:
            Dictionary containing session statistics
            
        Raises:
            VideoSession.DoesNotExist: If session not found
        """
        try:
            session = VideoSession.objects.prefetch_related(
                'participants', 'events'
            ).get(session_id=session_id)
        except VideoSession.DoesNotExist:
            raise VideoSession.DoesNotExist(f"Session with ID {session_id} not found")
        
        # Calculate session duration
        duration_minutes = None
        if session.started_at and session.ended_at:
            duration_minutes = (session.ended_at - session.started_at).total_seconds() / 60
        
        # Get participant statistics
        participants = session.participants.all()
        total_participants = participants.count()
        joined_participants = participants.filter(status='joined').count()
        left_participants = participants.filter(status='left').count()
        
        # Calculate average participation time
        total_participation_time = 0
        participation_count = 0
        
        for participant in participants:
            if participant.joined_at and participant.left_at:
                participation_time = (participant.left_at - participant.joined_at).total_seconds() / 60
                total_participation_time += participation_time
                participation_count += 1
        
        average_participation_time = total_participation_time / participation_count if participation_count > 0 else 0
        
        # Get event counts
        events = session.events.all()
        event_counts = {}
        for event in events:
            event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
        
        # Check if screen sharing was used
        screen_share_used = 'screen_share_started' in event_counts
        
        return {
            'session_id': str(session.session_id),
            'title': session.title,
            'session_type': session.session_type,
            'status': session.status,
            'host': session.host.username,
            'duration_minutes': round(duration_minutes, 2) if duration_minutes else None,
            'scheduled_time': session.scheduled_time,
            'started_at': session.started_at,
            'ended_at': session.ended_at,
            'participants': {
                'total': total_participants,
                'joined': joined_participants,
                'left': left_participants,
                'current': joined_participants if session.status == 'active' else 0
            },
            'average_participation_minutes': round(average_participation_time, 2),
            'total_participation_minutes': round(total_participation_time, 2),
            'events': {
                'total': events.count(),
                'by_type': event_counts
            },
            'features_used': {
                'screen_sharing': screen_share_used,
                'recording': session.is_recorded
            },
            'recording': {
                'is_recorded': session.is_recorded,
                'recording_url': session.recording_url if session.is_recorded else None,
                'recording_size_mb': round(session.recording_size_bytes / (1024 * 1024), 2) if session.recording_size_bytes else None
            }
        }


    @staticmethod
    def start_recording(session_id, user):
        """
        Start recording a video session.
        
        Args:
            session_id: UUID of the session
            user: User starting the recording (must be host)
            
        Returns:
            Updated VideoSession instance
            
        Raises:
            VideoSession.DoesNotExist: If session not found
            PermissionDenied: If user is not the host
            ValidationError: If recording cannot be started
            
        Requirements: 6.1, 6.2
        """
        try:
            session = VideoSession.objects.get(session_id=session_id)
        except VideoSession.DoesNotExist:
            raise VideoSession.DoesNotExist(f"Session with ID {session_id} not found")
        
        # Verify user is the host
        if session.host != user:
            raise PermissionDenied("Only the session host can start recording")
        
        # Validate session status
        if session.status != 'active':
            raise ValidationError("Can only record active sessions")
        
        # Check if already recording
        if session.is_recorded:
            raise ValidationError("Session is already being recorded")
        
        with transaction.atomic():
            # Update session
            session.is_recorded = True
            session.save(update_fields=['is_recorded', 'updated_at'])
            
            # Log recording start event
            VideoSessionEvent.objects.create(
                session=session,
                event_type='recording_started',
                user=user,
                details={
                    'action': 'recording_started',
                    'started_at': timezone.now().isoformat()
                }
            )
        
        return session
    
    @staticmethod
    def stop_recording(session_id, user):
        """
        Stop recording a video session.
        
        Args:
            session_id: UUID of the session
            user: User stopping the recording (must be host)
            
        Returns:
            Updated VideoSession instance
            
        Raises:
            VideoSession.DoesNotExist: If session not found
            PermissionDenied: If user is not the host
            ValidationError: If recording cannot be stopped
            
        Requirements: 6.1, 6.2
        """
        try:
            session = VideoSession.objects.get(session_id=session_id)
        except VideoSession.DoesNotExist:
            raise VideoSession.DoesNotExist(f"Session with ID {session_id} not found")
        
        # Verify user is the host
        if session.host != user:
            raise PermissionDenied("Only the session host can stop recording")
        
        # Validate session is being recorded
        if not session.is_recorded:
            raise ValidationError("Session is not being recorded")
        
        with transaction.atomic():
            # Log recording stop event
            VideoSessionEvent.objects.create(
                session=session,
                event_type='recording_stopped',
                user=user,
                details={
                    'action': 'recording_stopped',
                    'stopped_at': timezone.now().isoformat()
                }
            )
            
            # Note: is_recorded remains True as we have recorded content
            # The recording URL will be set when processing is complete
            session.save(update_fields=['updated_at'])
        
        return session
    
    @staticmethod
    def get_recording_url(session_id, user):
        """
        Get the recording URL for a session.
        
        Args:
            session_id: UUID of the session
            user: User requesting the recording
            
        Returns:
            Recording URL string or None
            
        Raises:
            VideoSession.DoesNotExist: If session not found
            PermissionDenied: If user doesn't have access to the recording
            
        Requirements: 6.4, 6.5
        """
        try:
            session = VideoSession.objects.get(session_id=session_id)
        except VideoSession.DoesNotExist:
            raise VideoSession.DoesNotExist(f"Session with ID {session_id} not found")
        
        # Check if user has access to this session
        is_participant = VideoSessionParticipant.objects.filter(
            session=session,
            user=user
        ).exists()
        
        if not is_participant and session.host != user:
            raise PermissionDenied("User does not have access to this recording")
        
        # Check if recording exists
        if not session.is_recorded or not session.recording_url:
            return None
        
        return session.recording_url
    
    @staticmethod
    def delete_recording(session_id, user):
        """
        Delete the recording for a session.
        
        Args:
            session_id: UUID of the session
            user: User deleting the recording (must be host)
            
        Returns:
            Updated VideoSession instance
            
        Raises:
            VideoSession.DoesNotExist: If session not found
            PermissionDenied: If user is not the host
            ValidationError: If recording cannot be deleted
            
        Requirements: 6.4, 6.5
        """
        import os
        import shutil
        from django.conf import settings
        
        try:
            session = VideoSession.objects.get(session_id=session_id)
        except VideoSession.DoesNotExist:
            raise VideoSession.DoesNotExist(f"Session with ID {session_id} not found")
        
        # Verify user is the host
        if session.host != user:
            raise PermissionDenied("Only the session host can delete recordings")
        
        # Check if recording exists
        if not session.is_recorded or not session.recording_url:
            raise ValidationError("No recording exists for this session")
        
        with transaction.atomic():
            # Delete recording files from storage
            recordings_dir = os.path.join(settings.MEDIA_ROOT, 'recordings', str(session.session_id))
            
            if os.path.exists(recordings_dir):
                try:
                    shutil.rmtree(recordings_dir)
                    logger.info(f"Deleted recording directory: {recordings_dir}")
                except Exception as e:
                    logger.error(f"Error deleting recording files: {str(e)}")
            
            # Update session
            session.is_recorded = False
            session.recording_url = ''
            session.recording_size_bytes = None
            session.save(update_fields=['is_recorded', 'recording_url', 'recording_size_bytes', 'updated_at'])
            
            # Log deletion event
            VideoSessionEvent.objects.create(
                session=session,
                event_type='recording_stopped',
                user=user,
                details={
                    'action': 'recording_deleted',
                    'deleted_at': timezone.now().isoformat()
                }
            )
        
        return session
    
    @staticmethod
    def get_recording_metadata(session_id, user):
        """
        Get metadata about a session recording.
        
        Args:
            session_id: UUID of the session
            user: User requesting the metadata
            
        Returns:
            Dictionary containing recording metadata
            
        Raises:
            VideoSession.DoesNotExist: If session not found
            PermissionDenied: If user doesn't have access
            
        Requirements: 6.4, 6.5
        """
        try:
            session = VideoSession.objects.get(session_id=session_id)
        except VideoSession.DoesNotExist:
            raise VideoSession.DoesNotExist(f"Session with ID {session_id} not found")
        
        # Check if user has access to this session
        is_participant = VideoSessionParticipant.objects.filter(
            session=session,
            user=user
        ).exists()
        
        if not is_participant and session.host != user:
            raise PermissionDenied("User does not have access to this recording")
        
        # Get recording events
        recording_started_event = session.events.filter(
            event_type='recording_started'
        ).first()
        
        recording_stopped_event = session.events.filter(
            event_type='recording_stopped'
        ).order_by('-timestamp').first()
        
        # Calculate recording duration
        recording_duration = None
        if recording_started_event and recording_stopped_event:
            duration_seconds = (recording_stopped_event.timestamp - recording_started_event.timestamp).total_seconds()
            recording_duration = round(duration_seconds / 60, 2)  # Convert to minutes
        
        return {
            'session_id': str(session.session_id),
            'session_title': session.title,
            'is_recorded': session.is_recorded,
            'recording_url': session.recording_url if session.is_recorded else None,
            'recording_size_bytes': session.recording_size_bytes,
            'recording_size_mb': round(session.recording_size_bytes / (1024 * 1024), 2) if session.recording_size_bytes else None,
            'recording_started_at': recording_started_event.timestamp if recording_started_event else None,
            'recording_stopped_at': recording_stopped_event.timestamp if recording_stopped_event else None,
            'recording_duration_minutes': recording_duration,
            'recorded_by': session.host.username,
            'is_available': session.is_recorded and bool(session.recording_url)
        }
    
    @staticmethod
    def create_session_report(session_id, reporter, report_type, description, 
                             reported_user=None, severity='medium'):
        """
        Create a report for inappropriate behavior or issues in a video session.
        
        Args:
            session_id: UUID of the session being reported
            reporter: User object submitting the report
            report_type: Type of report (from VideoSessionReport.REPORT_TYPE_CHOICES)
            description: Detailed description of the issue
            reported_user: Optional User object being reported
            severity: Severity level ('low', 'medium', 'high', 'critical')
            
        Returns:
            VideoSessionReport instance
            
        Raises:
            VideoSession.DoesNotExist: If session not found
            ValidationError: If validation fails
            PermissionDenied: If reporter is not a participant
            
        Requirements: 1.2, 2.3
        """
        from .models import VideoSessionReport
        
        try:
            session = VideoSession.objects.get(session_id=session_id)
        except VideoSession.DoesNotExist:
            raise VideoSession.DoesNotExist(f"Session with ID {session_id} not found")
        
        # Verify reporter is/was a participant in the session
        is_participant = VideoSessionParticipant.objects.filter(
            session=session,
            user=reporter
        ).exists()
        
        if not is_participant:
            raise PermissionDenied("Only session participants can submit reports")
        
        # Validate report type
        valid_types = [choice[0] for choice in VideoSessionReport.REPORT_TYPE_CHOICES]
        if report_type not in valid_types:
            raise ValidationError(f"Invalid report type. Must be one of: {valid_types}")
        
        # Validate severity
        valid_severities = ['low', 'medium', 'high', 'critical']
        if severity not in valid_severities:
            raise ValidationError(f"Invalid severity. Must be one of: {valid_severities}")
        
        # If reporting a user, verify they were in the session
        if reported_user:
            is_reported_participant = VideoSessionParticipant.objects.filter(
                session=session,
                user=reported_user
            ).exists()
            
            if not is_reported_participant:
                raise ValidationError("Reported user was not a participant in this session")
        
        with transaction.atomic():
            # Create the report
            report = VideoSessionReport.objects.create(
                session=session,
                reporter=reporter,
                reported_user=reported_user,
                report_type=report_type,
                description=description,
                severity=severity,
                status='pending'
            )
            
            # Log the report event
            VideoSessionEvent.objects.create(
                session=session,
                event_type='connection_issue',  # Using existing event type for now
                user=reporter,
                details={
                    'action': 'session_reported',
                    'report_id': report.id,
                    'report_type': report_type,
                    'severity': severity
                }
            )
            
            # Track disruption if reporting inappropriate behavior
            if report_type in ['inappropriate_behavior', 'harassment', 'bullying', 'spam']:
                from .rate_limiting import SessionAbuseDetector
                if reported_user:
                    disruption_count = SessionAbuseDetector.track_session_disruption(
                        reported_user,
                        session_id,
                        report_type
                    )
                    
                    # Auto-flag user if multiple reports
                    if disruption_count >= 3:
                        SessionAbuseDetector.flag_user(
                            reported_user,
                            f"Multiple reports received: {disruption_count} incidents",
                            duration_hours=24
                        )
        
        logger.info(
            f"Session report created: {report_type} in session {session_id} "
            f"by {reporter.username}" + 
            (f" against {reported_user.username}" if reported_user else "")
        )
        
        return report
    
    @staticmethod
    def get_session_reports(session_id, user=None, status=None):
        """
        Get reports for a specific session.
        
        Args:
            session_id: UUID of the session
            user: Optional user filter (to get reports by or against a user)
            status: Optional status filter
            
        Returns:
            QuerySet of VideoSessionReport objects
            
        Raises:
            VideoSession.DoesNotExist: If session not found
        """
        from .models import VideoSessionReport
        
        try:
            session = VideoSession.objects.get(session_id=session_id)
        except VideoSession.DoesNotExist:
            raise VideoSession.DoesNotExist(f"Session with ID {session_id} not found")
        
        reports = VideoSessionReport.objects.filter(session=session)
        
        if user:
            # Get reports by or against this user
            reports = reports.filter(
                models.Q(reporter=user) | models.Q(reported_user=user)
            )
        
        if status:
            reports = reports.filter(status=status)
        
        return reports.select_related('reporter', 'reported_user', 'reviewed_by').order_by('-created_at')
    
    @staticmethod
    def get_user_reports(user, as_reporter=True, as_reported=True, status=None):
        """
        Get all reports involving a specific user.
        
        Args:
            user: User object
            as_reporter: Include reports submitted by this user
            as_reported: Include reports against this user
            status: Optional status filter
            
        Returns:
            QuerySet of VideoSessionReport objects
        """
        from .models import VideoSessionReport
        from django.db.models import Q
        
        query = Q()
        
        if as_reporter:
            query |= Q(reporter=user)
        
        if as_reported:
            query |= Q(reported_user=user)
        
        reports = VideoSessionReport.objects.filter(query)
        
        if status:
            reports = reports.filter(status=status)
        
        return reports.select_related(
            'session', 'reporter', 'reported_user', 'reviewed_by'
        ).order_by('-created_at')
