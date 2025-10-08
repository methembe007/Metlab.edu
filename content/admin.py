from django.contrib import admin
from .models import UploadedContent, GeneratedSummary, GeneratedQuiz, Flashcard


@admin.register(UploadedContent)
class UploadedContentAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'user', 'content_type', 'processing_status', 'file_size', 'created_at']
    list_filter = ['content_type', 'processing_status', 'difficulty_level', 'created_at']
    search_fields = ['original_filename', 'user__username', 'subject']
    readonly_fields = ['file_size', 'original_filename', 'created_at', 'updated_at', 'processed_at']
    fieldsets = (
        ('File Information', {
            'fields': ('user', 'file', 'original_filename', 'content_type', 'file_size')
        }),
        ('Processing', {
            'fields': ('processing_status', 'processed_at', 'extracted_text')
        }),
        ('Content Details', {
            'fields': ('subject', 'difficulty_level', 'key_concepts')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GeneratedSummary)
class GeneratedSummaryAdmin(admin.ModelAdmin):
    list_display = ['content', 'summary_type', 'word_count', 'generated_at']
    list_filter = ['summary_type', 'generated_at']
    search_fields = ['content__original_filename', 'text']
    readonly_fields = ['word_count', 'generated_at']


@admin.register(GeneratedQuiz)
class GeneratedQuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'content', 'difficulty_level', 'question_count', 'estimated_time_minutes', 'generated_at']
    list_filter = ['difficulty_level', 'generated_at']
    search_fields = ['title', 'content__original_filename']
    readonly_fields = ['question_count', 'estimated_time_minutes', 'generated_at']


@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display = ['concept_tag', 'content', 'difficulty_level', 'order_index', 'created_at']
    list_filter = ['difficulty_level', 'created_at']
    search_fields = ['concept_tag', 'front_text', 'back_text', 'content__original_filename']
    ordering = ['content', 'order_index']
