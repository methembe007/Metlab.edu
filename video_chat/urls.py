"""
URL patterns for video chat application.
"""
from django.urls import path
from . import views
from .ice_servers import ice_servers_api

app_name = 'video_chat'

urlpatterns = [
    # Session scheduling and management (HTML views)
    path('schedule/', views.schedule_session, name='schedule_session'),
    path('quick-start/', views.quick_start_session, name='quick_start_session'),
    path('sessions/', views.session_list, name='session_list'),
    path('session/<uuid:session_id>/', views.session_detail, name='session_detail'),
    path('session/<uuid:session_id>/edit/', views.edit_session, name='edit_session'),
    path('session/<uuid:session_id>/cancel/', views.cancel_session, name='cancel_session'),
    path('session/<uuid:session_id>/join/', views.join_session, name='join_session'),
    path('session/<uuid:session_id>/calendar/', views.download_calendar, name='download_calendar'),
    
    # REST API endpoints for session management
    path('api/sessions/', views.api_session_list, name='api_session_list'),
    path('api/sessions/create/', views.api_create_session, name='api_create_session'),
    path('api/sessions/<uuid:session_id>/', views.api_session_detail, name='api_session_detail'),
    path('api/sessions/<uuid:session_id>/start/', views.api_start_session, name='api_start_session'),
    path('api/sessions/<uuid:session_id>/end/', views.api_end_session, name='api_end_session'),
    path('api/sessions/<uuid:session_id>/join/', views.api_join_session, name='api_join_session'),
    path('api/sessions/<uuid:session_id>/leave/', views.api_leave_session, name='api_leave_session'),
    path('api/sessions/<uuid:session_id>/participants/', views.api_session_participants, name='api_session_participants'),
    path('api/sessions/<uuid:session_id>/update-media/', views.api_update_media_state, name='api_update_media_state'),
    path('api/sessions/<uuid:session_id>/recording/start/', views.api_start_recording, name='api_start_recording'),
    path('api/sessions/<uuid:session_id>/recording/stop/', views.api_stop_recording, name='api_stop_recording'),
    path('api/sessions/<uuid:session_id>/statistics/', views.api_session_statistics, name='api_session_statistics'),
    
    # ICE servers configuration
    path('api/ice-servers/', ice_servers_api, name='ice_servers_api'),
]
