import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import VideoSession, VideoSessionParticipant, VideoSessionEvent

User = get_user_model()
logger = logging.getLogger(__name__)


class VideoSessionConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for video chat sessions.
    Handles WebRTC signaling, participant management, and session events.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = None
        self.session_group_name = None
        self.user = None
        self.session = None
        self.participant = None
    
    async def connect(self):
        """
        Handle WebSocket connection with authentication and authorization.
        Requirements: 1.2, 4.1, 4.2
        """
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.session_group_name = f'video_session_{self.session_id}'
        self.user = self.scope['user']
        
        # Check if user is authenticated
        if not self.user.is_authenticated:
            logger.warning(f"Unauthenticated connection attempt to session {self.session_id}")
            await self.close(code=4001)
            return
        
        try:
            # Get video session
            self.session = await self.get_video_session()
            
            if not self.session:
                logger.warning(f"Session {self.session_id} not found")
                await self.close(code=4004)
                return
            
            # Check if user is authorized to join this session
            if not await self.is_authorized_to_join():
                logger.warning(f"User {self.user.username} not authorized for session {self.session_id}")
                await self.close(code=4003)
                return
            
            # Check if session is active or scheduled
            if self.session.status not in ['scheduled', 'active']:
                logger.warning(f"Session {self.session_id} is {self.session.status}")
                await self.close(code=4005)
                return
            
            # Check if session is full
            if await self.is_session_full():
                logger.warning(f"Session {self.session_id} is full")
                await self.close(code=4006)
                return
            
            # Join room group
            await self.channel_layer.group_add(
                self.session_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            logger.info(f"User {self.user.username} connected to video session {self.session_id}")
            
        except Exception as e:
            logger.error(f"Error connecting to video session {self.session_id}: {str(e)}")
            await self.close(code=4000)
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if self.session_group_name and self.participant:
            # Update participant status
            await self.update_participant_status('left')
            
            # Log event
            await self.log_session_event('participant_left', {
                'user_id': str(self.user.id),
                'username': self.user.username,
                'close_code': close_code
            })
            
            # Notify other participants
            await self.channel_layer.group_send(
                self.session_group_name,
                {
                    'type': 'participant_left',
                    'user_id': str(self.user.id),
                    'username': self.user.get_full_name() or self.user.username,
                }
            )
            
            # Leave room group
            await self.channel_layer.group_discard(
                self.session_group_name,
                self.channel_name
            )
            
            logger.info(f"User {self.user.username} disconnected from video session {self.session_id}")
    
    async def receive(self, text_data):
        """
        Handle incoming WebSocket messages.
        Routes messages based on type.
        Requirements: 1.3, 4.3
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if not message_type:
                await self.send_error('Missing message type')
                return
            
            # Route message based on type
            if message_type == 'join':
                await self.handle_join(data)
            elif message_type == 'leave':
                await self.handle_leave(data)
            elif message_type == 'webrtc_offer':
                await self.handle_webrtc_offer(data)
            elif message_type == 'webrtc_answer':
                await self.handle_webrtc_answer(data)
            elif message_type == 'ice_candidate':
                await self.handle_ice_candidate(data)
            elif message_type == 'media_state':
                await self.handle_media_state(data)
            elif message_type == 'screen_share_start':
                await self.handle_screen_share_start(data)
            elif message_type == 'screen_share_stop':
                await self.handle_screen_share_stop(data)
            elif message_type == 'connection_quality':
                await self.handle_connection_quality(data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                await self.send_error(f'Unknown message type: {message_type}')
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {str(e)}")
            await self.send_error('Invalid JSON format')
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            await self.send_error('Internal server error')
    
    # Message Handlers
    
    async def handle_join(self, data):
        """
        Handle user joining the session.
        Requirements: 2.3, 7.1, 7.2, 7.3, 10.1, 10.2
        """
        try:
            # Create or update participant record
            self.participant = await self.create_or_update_participant()
            
            if not self.participant:
                await self.send_error('Failed to join session')
                return
            
            # Start session if not already active
            if self.session.status == 'scheduled':
                await self.start_session()
            
            # Log event
            await self.log_session_event('participant_joined', {
                'user_id': str(self.user.id),
                'username': self.user.username
            })
            
            # Get current participants
            participants = await self.get_current_participants()
            
            # Send current state to joining user
            await self.send(text_data=json.dumps({
                'type': 'joined',
                'session_id': str(self.session.session_id),
                'participants': participants,
                'user_id': str(self.user.id)
            }))
            
            # Notify other participants
            await self.channel_layer.group_send(
                self.session_group_name,
                {
                    'type': 'participant_joined',
                    'user_id': str(self.user.id),
                    'username': self.user.get_full_name() or self.user.username,
                    'audio_enabled': self.participant.audio_enabled,
                    'video_enabled': self.participant.video_enabled,
                }
            )
            
            logger.info(f"User {self.user.username} joined video session {self.session_id}")
            
        except Exception as e:
            logger.error(f"Error handling join: {str(e)}")
            await self.send_error('Failed to join session')
    
    async def handle_leave(self, data):
        """Handle user leaving the session"""
        try:
            await self.update_participant_status('left')
            
            # Log event
            await self.log_session_event('participant_left', {
                'user_id': str(self.user.id),
                'username': self.user.username
            })
            
            # Notify other participants
            await self.channel_layer.group_send(
                self.session_group_name,
                {
                    'type': 'participant_left',
                    'user_id': str(self.user.id),
                    'username': self.user.get_full_name() or self.user.username,
                }
            )
            
            # Close connection
            await self.close()
            
        except Exception as e:
            logger.error(f"Error handling leave: {str(e)}")
    
    async def handle_webrtc_offer(self, data):
        """
        Handle WebRTC offer for peer-to-peer connection.
        Requirements: 1.3, 4.3
        """
        try:
            target_user_id = data.get('target_user_id')
            offer = data.get('offer')
            
            if not target_user_id or not offer:
                await self.send_error('Missing target_user_id or offer')
                return
            
            # Validate offer structure
            if not isinstance(offer, dict) or 'type' not in offer or 'sdp' not in offer:
                await self.send_error('Invalid offer format')
                return
            
            # Send offer to target user
            await self.channel_layer.group_send(
                self.session_group_name,
                {
                    'type': 'webrtc_offer_message',
                    'offer': offer,
                    'from_user_id': str(self.user.id),
                    'from_username': self.user.get_full_name() or self.user.username,
                    'target_user_id': target_user_id,
                }
            )
            
            logger.debug(f"WebRTC offer from {self.user.username} to {target_user_id}")
            
        except Exception as e:
            logger.error(f"Error handling WebRTC offer: {str(e)}")
            await self.send_error('Failed to send offer')
    
    async def handle_webrtc_answer(self, data):
        """
        Handle WebRTC answer for peer-to-peer connection.
        Requirements: 1.3, 4.3
        """
        try:
            target_user_id = data.get('target_user_id')
            answer = data.get('answer')
            
            if not target_user_id or not answer:
                await self.send_error('Missing target_user_id or answer')
                return
            
            # Validate answer structure
            if not isinstance(answer, dict) or 'type' not in answer or 'sdp' not in answer:
                await self.send_error('Invalid answer format')
                return
            
            # Send answer to target user
            await self.channel_layer.group_send(
                self.session_group_name,
                {
                    'type': 'webrtc_answer_message',
                    'answer': answer,
                    'from_user_id': str(self.user.id),
                    'target_user_id': target_user_id,
                }
            )
            
            logger.debug(f"WebRTC answer from {self.user.username} to {target_user_id}")
            
        except Exception as e:
            logger.error(f"Error handling WebRTC answer: {str(e)}")
            await self.send_error('Failed to send answer')
    
    async def handle_ice_candidate(self, data):
        """
        Handle ICE candidate exchange for WebRTC connection.
        Requirements: 1.3, 4.3
        """
        try:
            target_user_id = data.get('target_user_id')
            candidate = data.get('candidate')
            
            if not target_user_id or not candidate:
                await self.send_error('Missing target_user_id or candidate')
                return
            
            # Send ICE candidate to target user
            await self.channel_layer.group_send(
                self.session_group_name,
                {
                    'type': 'ice_candidate_message',
                    'candidate': candidate,
                    'from_user_id': str(self.user.id),
                    'target_user_id': target_user_id,
                }
            )
            
            logger.debug(f"ICE candidate from {self.user.username} to {target_user_id}")
            
        except Exception as e:
            logger.error(f"Error handling ICE candidate: {str(e)}")
            await self.send_error('Failed to send ICE candidate')
    
    async def handle_media_state(self, data):
        """
        Handle media state changes (audio/video enable/disable).
        Requirements: 2.3, 7.1, 7.2, 7.3, 10.1, 10.2
        """
        try:
            audio_enabled = data.get('audio_enabled')
            video_enabled = data.get('video_enabled')
            
            # Update participant media state
            await self.update_media_state(audio_enabled, video_enabled)
            
            # Broadcast state change to all participants
            await self.channel_layer.group_send(
                self.session_group_name,
                {
                    'type': 'media_state_changed',
                    'user_id': str(self.user.id),
                    'audio_enabled': audio_enabled,
                    'video_enabled': video_enabled,
                }
            )
            
            logger.debug(f"Media state updated for {self.user.username}: audio={audio_enabled}, video={video_enabled}")
            
        except Exception as e:
            logger.error(f"Error handling media state: {str(e)}")
            await self.send_error('Failed to update media state')
    
    async def handle_screen_share_start(self, data):
        """
        Handle screen sharing start.
        Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
        """
        try:
            # Check if screen sharing is allowed
            if not self.session.allow_screen_share:
                await self.send_error('Screen sharing is not allowed in this session')
                return
            
            # Update participant screen sharing state
            await self.update_screen_sharing(True)
            
            # Log event
            await self.log_session_event('screen_share_started', {
                'user_id': str(self.user.id),
                'username': self.user.username
            })
            
            # Broadcast to all participants
            await self.channel_layer.group_send(
                self.session_group_name,
                {
                    'type': 'screen_share_started',
                    'user_id': str(self.user.id),
                    'username': self.user.get_full_name() or self.user.username,
                }
            )
            
            logger.info(f"Screen sharing started by {self.user.username} in session {self.session_id}")
            
        except Exception as e:
            logger.error(f"Error handling screen share start: {str(e)}")
            await self.send_error('Failed to start screen sharing')
    
    async def handle_screen_share_stop(self, data):
        """
        Handle screen sharing stop.
        Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
        """
        try:
            # Update participant screen sharing state
            await self.update_screen_sharing(False)
            
            # Log event
            await self.log_session_event('screen_share_stopped', {
                'user_id': str(self.user.id),
                'username': self.user.username
            })
            
            # Broadcast to all participants
            await self.channel_layer.group_send(
                self.session_group_name,
                {
                    'type': 'screen_share_stopped',
                    'user_id': str(self.user.id),
                }
            )
            
            logger.info(f"Screen sharing stopped by {self.user.username} in session {self.session_id}")
            
        except Exception as e:
            logger.error(f"Error handling screen share stop: {str(e)}")
            await self.send_error('Failed to stop screen sharing')
    
    async def handle_connection_quality(self, data):
        """
        Handle connection quality updates.
        Requirements: 10.1, 10.2
        """
        try:
            quality = data.get('quality', 'unknown')
            
            # Update participant connection quality
            await self.update_connection_quality(quality)
            
            logger.debug(f"Connection quality for {self.user.username}: {quality}")
            
        except Exception as e:
            logger.error(f"Error handling connection quality: {str(e)}")
    
    # Group message handlers (called by channel layer)
    
    async def participant_joined(self, event):
        """Send participant joined notification"""
        # Don't send to the user who joined
        if event['user_id'] != str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'participant_joined',
                'user_id': event['user_id'],
                'username': event['username'],
                'audio_enabled': event.get('audio_enabled', True),
                'video_enabled': event.get('video_enabled', True),
            }))
    
    async def participant_left(self, event):
        """Send participant left notification"""
        await self.send(text_data=json.dumps({
            'type': 'participant_left',
            'user_id': event['user_id'],
            'username': event['username'],
        }))
    
    async def webrtc_offer_message(self, event):
        """Send WebRTC offer to specific user"""
        if event['target_user_id'] == str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'webrtc_offer',
                'offer': event['offer'],
                'from_user_id': event['from_user_id'],
                'from_username': event['from_username'],
            }))
    
    async def webrtc_answer_message(self, event):
        """Send WebRTC answer to specific user"""
        if event['target_user_id'] == str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'webrtc_answer',
                'answer': event['answer'],
                'from_user_id': event['from_user_id'],
            }))
    
    async def ice_candidate_message(self, event):
        """Send ICE candidate to specific user"""
        if event['target_user_id'] == str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'ice_candidate',
                'candidate': event['candidate'],
                'from_user_id': event['from_user_id'],
            }))
    
    async def media_state_changed(self, event):
        """Send media state change notification"""
        # Don't send to the user who changed their state
        if event['user_id'] != str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'media_state_changed',
                'user_id': event['user_id'],
                'audio_enabled': event['audio_enabled'],
                'video_enabled': event['video_enabled'],
            }))
    
    async def screen_share_started(self, event):
        """Send screen share started notification"""
        await self.send(text_data=json.dumps({
            'type': 'screen_share_started',
            'user_id': event['user_id'],
            'username': event['username'],
        }))
    
    async def screen_share_stopped(self, event):
        """Send screen share stopped notification"""
        await self.send(text_data=json.dumps({
            'type': 'screen_share_stopped',
            'user_id': event['user_id'],
        }))
    
    # Helper methods
    
    async def send_error(self, message):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))
    
    # Database operations
    
    @database_sync_to_async
    def get_video_session(self):
        """Get video session by session_id"""
        try:
            return VideoSession.objects.get(session_id=self.session_id)
        except VideoSession.DoesNotExist:
            return None
    
    @database_sync_to_async
    def is_authorized_to_join(self):
        """
        Check if user is authorized to join this video session.
        Requirements: 1.2, 4.1, 4.2
        """
        if not self.session:
            return False
        
        # Host is always authorized
        if self.session.host == self.user:
            return True
        
        # Check if user is already a participant
        if VideoSessionParticipant.objects.filter(
            session=self.session,
            user=self.user
        ).exists():
            return True
        
        # For one-on-one sessions, check if user is invited
        if self.session.session_type == 'one_on_one':
            return VideoSessionParticipant.objects.filter(
                session=self.session,
                user=self.user,
                status='invited'
            ).exists()
        
        # For class sessions, check if user is enrolled in the class
        if self.session.session_type == 'class' and self.session.teacher_class:
            from learning.models import ClassEnrollment
            return ClassEnrollment.objects.filter(
                teacher_class=self.session.teacher_class,
                student__user=self.user,
                status='active'
            ).exists()
        
        # For group sessions, allow if not requiring approval
        if self.session.session_type == 'group' and not self.session.require_approval:
            return True
        
        return False
    
    @database_sync_to_async
    def is_session_full(self):
        """Check if session has reached maximum participants"""
        if not self.session:
            return True
        
        current_count = VideoSessionParticipant.objects.filter(
            session=self.session,
            status='joined'
        ).count()
        
        return current_count >= self.session.max_participants
    
    @database_sync_to_async
    def create_or_update_participant(self):
        """Create or update participant record"""
        try:
            participant, created = VideoSessionParticipant.objects.get_or_create(
                session=self.session,
                user=self.user,
                defaults={
                    'role': 'host' if self.session.host == self.user else 'participant',
                    'status': 'joined',
                    'joined_at': timezone.now()
                }
            )
            
            if not created and participant.status != 'joined':
                participant.status = 'joined'
                participant.joined_at = timezone.now()
                participant.save()
            
            return participant
            
        except Exception as e:
            logger.error(f"Error creating/updating participant: {str(e)}")
            return None
    
    @database_sync_to_async
    def update_participant_status(self, status):
        """Update participant status"""
        try:
            if self.participant:
                self.participant.status = status
                if status == 'left':
                    self.participant.left_at = timezone.now()
                self.participant.save()
        except Exception as e:
            logger.error(f"Error updating participant status: {str(e)}")
    
    @database_sync_to_async
    def update_media_state(self, audio_enabled, video_enabled):
        """Update participant media state"""
        try:
            if self.participant:
                if audio_enabled is not None:
                    self.participant.audio_enabled = audio_enabled
                if video_enabled is not None:
                    self.participant.video_enabled = video_enabled
                self.participant.save()
        except Exception as e:
            logger.error(f"Error updating media state: {str(e)}")
    
    @database_sync_to_async
    def update_screen_sharing(self, is_sharing):
        """Update participant screen sharing state"""
        try:
            if self.participant:
                self.participant.screen_sharing = is_sharing
                self.participant.save()
        except Exception as e:
            logger.error(f"Error updating screen sharing: {str(e)}")
    
    @database_sync_to_async
    def update_connection_quality(self, quality):
        """Update participant connection quality"""
        try:
            if self.participant:
                self.participant.connection_quality = quality
                self.participant.save()
        except Exception as e:
            logger.error(f"Error updating connection quality: {str(e)}")
    
    @database_sync_to_async
    def start_session(self):
        """Start the video session"""
        try:
            if self.session.status == 'scheduled':
                self.session.status = 'active'
                self.session.started_at = timezone.now()
                self.session.save()
                
                # Log event
                VideoSessionEvent.objects.create(
                    session=self.session,
                    event_type='session_started',
                    user=self.user,
                    details={'started_by': self.user.username}
                )
        except Exception as e:
            logger.error(f"Error starting session: {str(e)}")
    
    @database_sync_to_async
    def log_session_event(self, event_type, details):
        """Log session event"""
        try:
            VideoSessionEvent.objects.create(
                session=self.session,
                event_type=event_type,
                user=self.user,
                details=details
            )
        except Exception as e:
            logger.error(f"Error logging event: {str(e)}")
    
    @database_sync_to_async
    def get_current_participants(self):
        """Get list of current participants in the session"""
        try:
            participants = []
            for participant in VideoSessionParticipant.objects.filter(
                session=self.session,
                status='joined'
            ).select_related('user'):
                participants.append({
                    'user_id': str(participant.user.id),
                    'username': participant.user.get_full_name() or participant.user.username,
                    'role': participant.role,
                    'audio_enabled': participant.audio_enabled,
                    'video_enabled': participant.video_enabled,
                    'screen_sharing': participant.screen_sharing,
                    'connection_quality': participant.connection_quality,
                })
            return participants
        except Exception as e:
            logger.error(f"Error getting participants: {str(e)}")
            return []
