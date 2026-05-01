from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/study-room/(?P<room_id>\w+)/$', consumers.StudyRoomConsumer.as_asgi()),
]