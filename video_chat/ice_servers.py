"""
ICE Server Configuration Utility

This module provides utilities for accessing WebRTC ICE server configuration
from Django settings and making it available to the frontend.
"""

from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


def get_ice_servers():
    """
    Get ICE server configuration from Django settings.
    
    Returns:
        list: List of ICE server configurations
    """
    return getattr(settings, 'WEBRTC_ICE_SERVERS', [
        {'urls': 'stun:stun.l.google.com:19302'},
        {'urls': 'stun:stun1.l.google.com:19302'},
    ])


@login_required
def ice_servers_api(request):
    """
    API endpoint to provide ICE server configuration to authenticated users.
    
    Args:
        request: Django HTTP request
        
    Returns:
        JsonResponse: ICE server configuration
    """
    from .sfu_config import SFUConfig
    
    ice_servers = get_ice_servers()
    
    # Filter out sensitive credentials for logging
    safe_servers = []
    for server in ice_servers:
        safe_server = {'urls': server['urls']}
        if 'username' in server:
            safe_server['username'] = server['username']
        if 'credential' in server:
            safe_server['credential'] = server['credential']
        safe_servers.append(safe_server)
    
    # Get session_id from query params to determine connection mode
    session_id = request.GET.get('session_id')
    connection_mode = 'p2p'
    
    if session_id:
        try:
            from .models import VideoSession
            session = VideoSession.objects.get(session_id=session_id)
            connection_mode = SFUConfig.get_connection_mode(session)
        except VideoSession.DoesNotExist:
            pass
    
    return JsonResponse({
        'iceServers': safe_servers,
        'maxParticipants': getattr(settings, 'VIDEO_CHAT_MAX_PARTICIPANTS', 30),
        'sessionTimeout': getattr(settings, 'VIDEO_CHAT_SESSION_TIMEOUT', 3600),
        'recordingEnabled': getattr(settings, 'VIDEO_CHAT_RECORDING_ENABLED', True),
        'screenShareEnabled': getattr(settings, 'VIDEO_CHAT_SCREEN_SHARE_ENABLED', True),
        'connectionMode': connection_mode,
        'sfuConfig': SFUConfig.get_sfu_config(),
    })


def get_video_chat_settings():
    """
    Get all video chat related settings.
    
    Returns:
        dict: Video chat configuration settings
    """
    return {
        'ice_servers': get_ice_servers(),
        'max_participants': getattr(settings, 'VIDEO_CHAT_MAX_PARTICIPANTS', 30),
        'session_timeout': getattr(settings, 'VIDEO_CHAT_SESSION_TIMEOUT', 3600),
        'recording_enabled': getattr(settings, 'VIDEO_CHAT_RECORDING_ENABLED', True),
        'screen_share_enabled': getattr(settings, 'VIDEO_CHAT_SCREEN_SHARE_ENABLED', True),
    }
