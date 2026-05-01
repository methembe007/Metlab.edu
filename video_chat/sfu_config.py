"""
SFU (Selective Forwarding Unit) Configuration
Handles routing logic between P2P and SFU modes based on participant count.
"""
from django.conf import settings


class SFUConfig:
    """Configuration for SFU mode selection"""
    
    # Threshold for switching from P2P to SFU
    P2P_MAX_PARTICIPANTS = getattr(settings, 'VIDEO_CHAT_P2P_MAX_PARTICIPANTS', 6)
    
    # SFU server configuration
    SFU_ENABLED = getattr(settings, 'VIDEO_CHAT_SFU_ENABLED', False)
    SFU_SERVER_URL = getattr(settings, 'VIDEO_CHAT_SFU_SERVER_URL', 'http://localhost:3000')
    SFU_SERVER_API_KEY = getattr(settings, 'VIDEO_CHAT_SFU_SERVER_API_KEY', '')
    
    @classmethod
    def should_use_sfu(cls, participant_count):
        """
        Determine if SFU should be used based on participant count.
        
        Args:
            participant_count: Number of participants in the session
            
        Returns:
            bool: True if SFU should be used, False for P2P
        """
        if not cls.SFU_ENABLED:
            return False
        
        return participant_count > cls.P2P_MAX_PARTICIPANTS
    
    @classmethod
    def get_connection_mode(cls, session):
        """
        Get the connection mode for a session.
        
        Args:
            session: VideoSession instance
            
        Returns:
            str: 'p2p' or 'sfu'
        """
        participant_count = session.participants.filter(status='joined').count()
        
        if cls.should_use_sfu(participant_count):
            return 'sfu'
        return 'p2p'
    
    @classmethod
    def validate_session_size(cls, session_type, max_participants):
        """
        Validate session size based on available infrastructure.
        
        Args:
            session_type: Type of session
            max_participants: Requested max participants
            
        Returns:
            tuple: (is_valid, error_message)
        """
        # If SFU is not enabled, limit to P2P max
        if not cls.SFU_ENABLED:
            if max_participants > cls.P2P_MAX_PARTICIPANTS:
                return False, (
                    f"Sessions are currently limited to {cls.P2P_MAX_PARTICIPANTS} participants. "
                    f"Please contact support for larger sessions."
                )
        
        # Hard limit even with SFU
        hard_limit = 30
        if max_participants > hard_limit:
            return False, f"Maximum {hard_limit} participants allowed per session."
        
        return True, None
    
    @classmethod
    def get_sfu_config(cls):
        """
        Get SFU server configuration for frontend.
        
        Returns:
            dict: SFU configuration
        """
        return {
            'enabled': cls.SFU_ENABLED,
            'server_url': cls.SFU_SERVER_URL,
            'p2p_max_participants': cls.P2P_MAX_PARTICIPANTS,
        }
