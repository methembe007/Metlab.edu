from django.urls import path
from . import views

app_name = 'learning'

urlpatterns = [
    # Session tracking API endpoints
    path('session/start/', views.SessionTrackingView.as_view(), name='start_session'),
    path('session/<int:session_id>/update/', views.SessionTrackingView.as_view(), name='update_session'),
    path('session/<int:session_id>/complete/', views.SessionTrackingView.as_view(), name='complete_session'),
    
    # Daily lesson endpoints
    path('daily-lesson/', views.daily_lesson_view, name='daily_lesson'),
    path('lesson/<int:lesson_id>/', views.lesson_detail_view, name='lesson_detail'),
    path('lesson-history/', views.lesson_history_view, name='lesson_history'),
    path('api/lesson/<int:lesson_id>/start/', views.start_daily_lesson, name='start_daily_lesson'),
    path('api/lesson/<int:lesson_id>/complete/', views.complete_daily_lesson, name='complete_daily_lesson'),
    path('api/lesson/<int:lesson_id>/progress/', views.record_lesson_progress, name='record_lesson_progress'),
    path('api/lesson/<int:lesson_id>/skip/', views.skip_daily_lesson, name='skip_daily_lesson'),
    path('api/lesson/<int:lesson_id>/analytics/', views.lesson_analytics_api, name='lesson_analytics'),
    
    # Analytics and recommendations
    path('analytics/', views.student_analytics_view, name='analytics'),
    path('teacher-analytics/', views.teacher_analytics_view, name='teacher_analytics'),
    path('parent-analytics/', views.parent_analytics_view, name='parent_analytics'),
    path('api/recommendations/', views.get_recommendations, name='get_recommendations'),
    path('api/recommendations/<int:recommendation_id>/viewed/', views.mark_recommendation_viewed, name='mark_recommendation_viewed'),
    
    # Practice endpoints
    path('practice/', views.practice_concept_view, name='practice_concept'),
]