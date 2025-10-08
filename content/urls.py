from django.urls import path
from . import views

app_name = 'content'

urlpatterns = [
    # Content upload and management
    path('upload/', views.upload_content, name='upload'),
    path('library/', views.content_library, name='library'),
    path('detail/<int:content_id>/', views.content_detail, name='detail'),
    path('download/<int:content_id>/', views.download_content, name='download'),
    path('delete/<int:content_id>/', views.delete_content, name='delete'),
    
    # AJAX endpoints
    path('status/<int:content_id>/', views.processing_status, name='status'),
    path('upload-progress/', views.upload_progress, name='upload_progress'),
    
    # Learning materials
    path('quiz/<int:quiz_id>/', views.quiz_view, name='quiz'),
    path('flashcards/<int:content_id>/', views.flashcards_view, name='flashcards'),
]