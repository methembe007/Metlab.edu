import json
import logging
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from accounts.models import StudentProfile
from .models import StudySession, StudySessionAttendance, StudyRoomReport

User = get_user_model()
logger = logging.getLogger(__name__)


class StudyRoomConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_id = None
        self.room_group_name = None
        self.user = None
        self.student_profile = None
        self.session = None
        self.is_moderator = False
            
 
   async def connect(self):
        """Handle WebSocket connection"""
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'study_room_{self.room_id}'
        self.user = self.scope['user']
        
        # Check if user is authenticated
        if not self.user.is_authenticated:
            await self.close()
            return
        
        try:
            # Get student profile and session
            self.student_profile = await self.get_student_profile()
            self.session = await self.get_study_session()
            
            if not self.student_profile or not self.session:
                await self.close()
                return
            
            # Check if user is authorized to join this room
            if not await self.is_authorized_to_join():
                await self.close()
                return
            
            # Set moderator status
            self.is_moderator = await self.check_moderator_status()
            
            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            # Update session attendance
            await self.update_attendance('joined')
            
            logger.info(f"User {self.user.username} connected to study room {self.room_id}")
            
        except Exception as e:
            logger.error(f"Error connecting to study room {self.room_id}: {str(e)}")
            await self.close()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if self.room_group_name:
            # Update attendance
            await self.update_attendance('left')
            
            # Notify other participants
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_left',
                    'userId': str(self.user.id),
                    'userName': self.user.get_full_name() or self.user.username,
                }
            )
            
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            
            logger.info(f"User {self.user.username} disconnected from study room {self.room_id}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # Route message based on type
            if message_type == 'join':
                await self.handle_join(data)
            elif message_type == 'offer':
                await self.handle_webrtc_offer(data)
            elif message_type == 'answer':
                await self.handle_webrtc_answer(data)
            elif message_type == 'ice-candidate':
                await self.handle_ice_candidate(data)
            elif message_type == 'chat-message':
                await self.handle_chat_message(data)
            elif message_type == 'screen-share-start':
                await self.handle_screen_share_start(data)
            elif message_type == 'screen-share-stop':
                await self.handle_screen_share_stop(data)
            elif message_type == 'moderation-action':
                await self.handle_moderation_action(data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
    
    async def handle_join(self, data):
        """Handle user joining the room"""
        # Notify other participants
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'userId': str(self.user.id),
                'userName': self.user.get_full_name() or self.user.username,
            }
        )
        
        # Send current participants list to new user
        participants = await self.get_current_participants()
        await self.send(text_data=json.dumps({
            'type': 'participants-update',
            'participants': participants
        }))
    
    async def handle_webrtc_offer(self, data):
        """Handle WebRTC offer for peer-to-peer connection"""
        target_user_id = data.get('targetUserId')
        offer = data.get('offer')
        
        if target_user_id and offer:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'webrtc_offer',
                    'offer': offer,
                    'userId': str(self.user.id),
                    'userName': self.user.get_full_name() or self.user.username,
                    'targetUserId': target_user_id,
                }
            )
    
    async def handle_webrtc_answer(self, data):
        """Handle WebRTC answer for peer-to-peer connection"""
        target_user_id = data.get('targetUserId')
        answer = data.get('answer')
        
        if target_user_id and answer:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'webrtc_answer',
                    'answer': answer,
                    'userId': str(self.user.id),
                    'targetUserId': target_user_id,
                }
            )
    
    async def handle_ice_candidate(self, data):
        """Handle ICE candidate for WebRTC connection"""
        target_user_id = data.get('targetUserId')
        candidate = data.get('candidate')
        
        if target_user_id and candidate:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'ice_candidate',
                    'candidate': candidate,
                    'userId': str(self.user.id),
                    'targetUserId': target_user_id,
                }
            )
    
    async def handle_chat_message(self, data):
        """Handle chat message in study room"""
        message = data.get('message', '').strip()
        
        if not message:
            return
        
        # Basic content filtering
        if await self.is_message_inappropriate(message):
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Message contains inappropriate content and was not sent.'
            }))
            return
        
        # Broadcast message to all participants
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'userId': str(self.user.id),
                'userName': self.user.get_full_name() or self.user.username,
                'timestamp': timezone.now().isoformat(),
            }
        )
    
    async def handle_screen_share_start(self, data):
        """Handle screen sharing start"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'screen_share_start',
                'userId': str(self.user.id),
                'userName': self.user.get_full_name() or self.user.username,
            }
        )
    
    async def handle_screen_share_stop(self, data):
        """Handle screen sharing stop"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'screen_share_stop',
                'userId': str(self.user.id),
            }
        )
    
    async def handle_moderation_action(self, data):
        """Handle moderation actions (mute, kick, etc.)"""
        if not self.is_moderator:
            return
        
        action = data.get('action')
        target_user_id = data.get('targetUserId')
        reason = data.get('reason', 'No reason provided')
        
        if action and target_user_id:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'moderation_action',
                    'action': action,
                    'targetUserId': target_user_id,
                    'reason': reason,
                    'moderatorId': str(self.user.id),
                    'moderatorName': self.user.get_full_name() or self.user.username,
                }
            )
    
    # Group message handlers (called by channel layer)
    async def user_joined(self, event):
        """Send user joined notification"""
        await self.send(text_data=json.dumps({
            'type': 'user-joined',
            'userId': event['userId'],
            'userName': event['userName'],
        }))
    
    async def user_left(self, event):
        """Send user left notification"""
        await self.send(text_data=json.dumps({
            'type': 'user-left',
            'userId': event['userId'],
            'userName': event['userName'],
        }))
    
    async def webrtc_offer(self, event):
        """Send WebRTC offer to specific user"""
        if event['targetUserId'] == str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'offer',
                'offer': event['offer'],
                'userId': event['userId'],
                'userName': event['userName'],
            }))
    
    async def webrtc_answer(self, event):
        """Send WebRTC answer to specific user"""
        if event['targetUserId'] == str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'answer',
                'answer': event['answer'],
                'userId': event['userId'],
            }))
    
    async def ice_candidate(self, event):
        """Send ICE candidate to specific user"""
        if event['targetUserId'] == str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'ice-candidate',
                'candidate': event['candidate'],
                'userId': event['userId'],
            }))
    
    async def chat_message(self, event):
        """Send chat message to all users"""
        await self.send(text_data=json.dumps({
            'type': 'chat-message',
            'message': event['message'],
            'userId': event['userId'],
            'userName': event['userName'],
            'timestamp': event['timestamp'],
        }))
    
    async def screen_share_start(self, event):
        """Send screen share start notification"""
        await self.send(text_data=json.dumps({
            'type': 'screen-share-start',
            'userId': event['userId'],
            'userName': event['userName'],
        }))
    
    async def screen_share_stop(self, event):
        """Send screen share stop notification"""
        await self.send(text_data=json.dumps({
            'type': 'screen-share-stop',
            'userId': event['userId'],
        }))
    
    async def moderation_action(self, event):
        """Send moderation action notification"""
        await self.send(text_data=json.dumps({
            'type': 'moderation-action',
            'action': event['action'],
            'targetUserId': event['targetUserId'],
            'reason': event['reason'],
            'moderatorId': event['moderatorId'],
            'moderatorName': event['moderatorName'],
        }))
    
    # Database operations
    @database_sync_to_async
    def get_student_profile(self):
        """Get student profile for the current user"""
        try:
            return StudentProfile.objects.get(user=self.user)
        except StudentProfile.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_study_session(self):
        """Get study session by room ID"""
        try:
            return StudySession.objects.get(room_id=self.room_id)
        except StudySession.DoesNotExist:
            return None
    
    @database_sync_to_async
    def is_authorized_to_join(self):
        """Check if user is authorized to join this study room"""
        if not self.session or not self.student_profile:
            return False
        
        # Check if user is a participant in the session
        participants = self.session.get_participants()
        return self.student_profile in participants
    
    @database_sync_to_async
    def check_moderator_status(self):
        """Check if user has moderator privileges in this room"""
        if not self.session or not self.student_profile:
            return False
        
        # Session creator is always a moderator
        if self.session.created_by == self.student_profile:
            return True
        
        # For group sessions, check if user is admin/moderator
        if (self.session.session_type == 'group' and 
            self.session.study_group):
            membership = self.session.study_group.memberships.filter(
                student=self.student_profile,
                status='active',
                role__in=['admin', 'moderator']
            ).first()
            return membership is not None
        
        return False
    
    @database_sync_to_async
    def update_attendance(self, action):
        """Update session attendance record"""
        try:
            attendance, created = StudySessionAttendance.objects.get_or_create(
                session=self.session,
                student=self.student_profile,
                defaults={'status': 'invited'}
            )
            
            if action == 'joined':
                attendance.status = 'attended'
                attendance.joined_at = timezone.now()
                attendance.save()
            elif action == 'left' and attendance.joined_at:
                attendance.left_at = timezone.now()
                attendance.save()
                
        except Exception as e:
            logger.error(f"Error updating attendance: {str(e)}")
    
    @database_sync_to_async
    def get_current_participants(self):
        """Get list of current participants in the session"""
        try:
            participants = []
            for participant in self.session.get_participants():
                participants.append({
                    'userId': str(participant.user.id),
                    'userName': participant.user.get_full_name() or participant.user.username,
                    'isModerator': participant == self.session.created_by
                })
            return participants
        except Exception as e:
            logger.error(f"Error getting participants: {str(e)}")
            return []
    
    @database_sync_to_async
    def is_message_inappropriate(self, message):
        """Basic content filtering for chat messages"""
        # Simple keyword filtering - in production, use more sophisticated filtering
        inappropriate_words = [
            'spam', 'scam', 'hack', 'cheat', 'inappropriate',
            # Add more words as needed
        ]
        
        message_lower = message.lower()
        return any(word in message_lower for word in inappropriate_words)
    
    @database_sync_to_async
    def create_report(self, issue_type, description):
        """Create a study room report"""
        try:
            report = StudyRoomReport.objects.create(
                session=self.session,
                reporter=self.student_profile,
                issue_type=issue_type,
                description=description
            )
            return report
        except Exception as e:
            logger.error(f"Error creating report: {str(e)}")
            return None