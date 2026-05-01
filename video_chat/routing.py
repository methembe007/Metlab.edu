"""
WebSocket routing configuration for video chat application.
Handles WebSocket connections for real-time video session signaling.
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # WebSocket endpoint for video session signaling
    # Requirements: 1.2, 1.3, 4.1, 4.3
    re_path(r'ws/video/(?P<session_id>[0-9a-f-]+)/$', consumers.VideoSessionConsumer.as_asgi()),
]