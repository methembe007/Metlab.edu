from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    # Tutor recommendation and search
    path('tutors/', views.tutor_recommendations, name='tutor_recommendations'),
    path('tutors/<int:tutor_id>/', views.tutor_detail, name='tutor_detail'),
    path('tutors/search/', views.tutor_search_api, name='tutor_search_api'),
    
    # Booking management
    path('tutors/<int:tutor_id>/book/', views.book_tutor, name='book_tutor'),
    path('bookings/', views.my_bookings, name='my_bookings'),
    path('bookings/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('bookings/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('bookings/<int:booking_id>/review/', views.review_tutor, name='review_tutor'),
    
    # Study partner matching and management
    path('study-partners/', views.study_partner_recommendations, name='study_partner_recommendations'),
    path('study-partners/request/', views.send_partner_request, name='send_partner_request'),
    path('study-partners/requests/', views.partner_requests, name='partner_requests'),
    path('study-partners/requests/<int:request_id>/respond/', views.respond_to_partner_request, name='respond_to_partner_request'),
    path('study-partners/requests/<int:request_id>/cancel/', views.cancel_partner_request, name='cancel_partner_request'),
    path('study-partners/my-partners/', views.my_study_partners, name='my_study_partners'),
    
    # Study session management
    path('study-partners/<int:partnership_id>/schedule/', views.schedule_study_session, name='schedule_study_session'),
    path('study-sessions/', views.my_study_sessions, name='my_study_sessions'),
    path('study-sessions/<int:session_id>/', views.study_session_detail, name='study_session_detail'),
    
    # Study group management
    path('study-groups/', views.study_groups, name='study_groups'),
    path('study-groups/create/', views.create_study_group, name='create_study_group'),
    path('study-groups/my-groups/', views.my_study_groups, name='my_study_groups'),
    path('study-groups/<int:group_id>/', views.study_group_detail, name='study_group_detail'),
    path('study-groups/<int:group_id>/join/', views.join_study_group, name='join_study_group'),
    path('study-groups/<int:group_id>/leave/', views.leave_study_group, name='leave_study_group'),
    
    # Study group chat
    path('study-groups/<int:group_id>/messages/', views.get_group_messages, name='get_group_messages'),
    path('study-groups/<int:group_id>/send-message/', views.send_group_message, name='send_group_message'),
    
    # Group study sessions
    path('study-groups/<int:group_id>/schedule-session/', views.schedule_group_session, name='schedule_group_session'),
    path('group-sessions/<int:session_id>/', views.group_session_detail, name='group_session_detail'),
    path('group-sessions/<int:session_id>/attendance/', views.update_session_attendance, name='update_session_attendance'),
    
    # Real-time study rooms
    path('study-room/<int:session_id>/', views.study_room, name='study_room'),
    path('study-room/js/', views.study_room_js, name='study_room_js'),
    
    # Study room moderation
    path('api/study-room/report/', views.report_study_room_issue, name='report_study_room_issue'),
]