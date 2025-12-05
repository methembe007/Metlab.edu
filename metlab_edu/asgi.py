"""
ASGI config for metlab_edu project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from community.routing import websocket_urlpatterns as community_websocket_urlpatterns
from video_chat.routing import websocket_urlpatterns as video_chat_websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'metlab_edu.settings')

# Combine all WebSocket URL patterns
websocket_urlpatterns = community_websocket_urlpatterns + video_chat_websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
