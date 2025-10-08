from django.urls import path
from . import views
from . import teacher_views
from . import parent_views

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
    
    # Teacher content management
    path('teacher/', teacher_views.teacher_content_dashboard, name='teacher_content_dashboard'),
    path('teacher/upload/', teacher_views.upload_content, name='upload_content'),
    path('teacher/content/', teacher_views.content_list, name='teacher_content_list'),
    path('teacher/content/<int:content_id>/', teacher_views.content_detail, name='teacher_content_detail'),
    path('teacher/quiz/<int:quiz_id>/customize/', teacher_views.customize_quiz, name='customize_quiz'),
    path('teacher/quizzes/', teacher_views.quiz_list, name='teacher_quiz_list'),
    path('teacher/quiz/<int:quiz_id>/toggle/', teacher_views.toggle_quiz_status, name='toggle_quiz_status'),
    path('teacher/quiz/<int:quiz_id>/analytics/', teacher_views.quiz_analytics, name='quiz_analytics'),
    
    # Class management
    path('teacher/classes/', teacher_views.class_management, name='class_management'),
    path('teacher/classes/create/', teacher_views.create_class, name='create_class'),
    path('teacher/classes/<int:class_id>/', teacher_views.class_detail, name='class_detail'),
    path('teacher/classes/<int:class_id>/progress/', teacher_views.student_progress, name='student_progress'),
    path('teacher/classes/<int:class_id>/remove/<int:student_id>/', teacher_views.remove_student, name='remove_student'),
    path('teacher/distribute/', teacher_views.bulk_content_distribution, name='bulk_content_distribution'),
    
    # Parent monitoring dashboard
    path('parent/', parent_views.parent_dashboard, name='parent_dashboard'),
    path('parent/child/<int:child_id>/progress/', parent_views.child_progress_detail, name='child_progress_detail'),
    path('parent/child/<int:child_id>/screen-time/', parent_views.screen_time_settings, name='screen_time_settings'),
    path('parent/notifications/', parent_views.notification_settings, name='notification_settings'),
    path('parent/link-child/', parent_views.link_child_account, name='link_child_account'),
    path('parent/child/<int:child_id>/unlink/', parent_views.unlink_child_account, name='unlink_child_account'),
    path('parent/child/<int:child_id>/encourage/', parent_views.send_encouragement_message, name='send_encouragement_message'),
    
    # Parent AJAX endpoints
    path('parent/child/<int:child_id>/screen-time-data/', parent_views.get_child_screen_time, name='get_child_screen_time'),
    path('parent/child/<int:child_id>/performance-data/', parent_views.get_child_performance_data, name='get_child_performance_data'),
    
    # AJAX endpoints
    path('api/quiz/update/', teacher_views.update_quiz_questions, name='update_quiz_questions'),
    path('api/class/<int:class_id>/students/', teacher_views.get_class_students, name='get_class_students'),
    path('api/content/<int:content_id>/status/', teacher_views.content_processing_status, name='content_processing_status'),
]