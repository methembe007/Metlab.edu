from django.urls import path
from . import views
from . import privacy_views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-email/<str:uidb64>/<str:token>/', views.verify_email, name='verify_email'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    path('dashboard/teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('dashboard/parent/', views.parent_dashboard, name='parent_dashboard'),
    
    # Privacy and compliance URLs
    path('privacy/', privacy_views.privacy_settings, name='privacy_settings'),
    path('privacy/update-consent/', privacy_views.update_consent, name='update_consent'),
    path('privacy/request-deletion/', privacy_views.request_data_deletion, name='request_data_deletion'),
    path('privacy/request-export/', privacy_views.request_data_export, name='request_data_export'),
    path('privacy/download-export/<int:request_id>/', privacy_views.download_data_export, name='download_data_export'),
    path('privacy/coppa-verification/', privacy_views.coppa_parent_verification, name='coppa_parent_verification'),
    path('privacy/audit-log/', privacy_views.audit_log, name='audit_log'),
]