from django.contrib import admin
from .models import LearningSession, WeaknessAnalysis, PersonalizedRecommendation, DailyLesson, LessonProgress


@admin.register(LearningSession)
class LearningSessionAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'content', 'session_type', 'status', 
        'performance_score', 'time_spent_minutes', 'xp_earned', 'start_time'
    ]
    list_filter = [
        'session_type', 'status', 'difficulty_level', 'start_time'
    ]
    search_fields = [
        'student__user__username', 'content__original_filename', 'concepts_covered'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Session Info', {
            'fields': ('student', 'content', 'session_type', 'status', 'difficulty_level')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time', 'time_spent_minutes')
        }),
        ('Performance', {
            'fields': ('questions_attempted', 'questions_correct', 'performance_score', 'xp_earned')
        }),
        ('Content', {
            'fields': ('concepts_covered',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(WeaknessAnalysis)
class WeaknessAnalysisAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'subject', 'concept', 'weakness_level', 
        'weakness_score', 'priority_level', 'improvement_trend', 'last_updated'
    ]
    list_filter = [
        'weakness_level', 'improvement_trend', 'priority_level', 'subject'
    ]
    search_fields = [
        'student__user__username', 'subject', 'concept'
    ]
    readonly_fields = ['created_at', 'last_updated']
    
    fieldsets = (
        ('Student & Concept', {
            'fields': ('student', 'subject', 'concept')
        }),
        ('Analysis', {
            'fields': ('weakness_score', 'weakness_level', 'priority_level', 'improvement_trend')
        }),
        ('Performance Data', {
            'fields': ('total_attempts', 'correct_attempts', 'last_attempt_score')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_updated'),
            'classes': ('collapse',)
        })
    )


@admin.register(PersonalizedRecommendation)
class PersonalizedRecommendationAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'title', 'recommendation_type', 'priority', 
        'status', 'estimated_time_minutes', 'created_at'
    ]
    list_filter = [
        'recommendation_type', 'status', 'priority', 'created_at'
    ]
    search_fields = [
        'student__user__username', 'title', 'description'
    ]
    readonly_fields = ['created_at', 'updated_at', 'viewed_at', 'completed_at']
    
    fieldsets = (
        ('Recommendation Info', {
            'fields': ('student', 'recommendation_type', 'title', 'description', 'priority')
        }),
        ('Content & Relations', {
            'fields': ('content', 'related_weakness', 'related_content')
        }),
        ('Status & Timing', {
            'fields': ('status', 'estimated_time_minutes', 'expires_at')
        }),
        ('Tracking', {
            'fields': ('viewed_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(DailyLesson)
class DailyLessonAdmin(admin.ModelAdmin):
    list_display = ['student', 'lesson_date', 'lesson_type', 'title', 'status', 'performance_score', 'xp_earned']
    list_filter = ['lesson_date', 'lesson_type', 'status', 'difficulty_level']
    search_fields = ['student__user__username', 'title', 'priority_concepts']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('student', 'lesson_date', 'lesson_type', 'title', 'description')
        }),
        ('Lesson Content', {
            'fields': ('content_structure', 'estimated_duration_minutes', 'difficulty_level', 'priority_concepts'),
            'classes': ('collapse',)
        }),
        ('Progress Tracking', {
            'fields': ('status', 'started_at', 'completed_at', 'performance_score', 'time_spent_minutes', 'xp_earned')
        }),
        ('Relationships', {
            'fields': ('related_content', 'related_weaknesses'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student__user')


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ['lesson', 'activity_type', 'activity_index', 'concept', 'is_correct', 'time_spent_seconds']
    list_filter = ['activity_type', 'is_correct', 'difficulty_rating', 'completed_at']
    search_fields = ['lesson__title', 'concept', 'question_text']
    readonly_fields = ['completed_at']
    
    fieldsets = (
        ('Activity Information', {
            'fields': ('lesson', 'activity_type', 'activity_index', 'concept')
        }),
        ('Content', {
            'fields': ('question_text', 'student_answer', 'correct_answer', 'is_correct')
        }),
        ('Performance', {
            'fields': ('time_spent_seconds', 'difficulty_rating', 'completed_at')
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('lesson__student__user')