from django.contrib import admin
from .models import LearningSession, WeaknessAnalysis, PersonalizedRecommendation, DailyLesson, LessonProgress
from .teacher_models import TeacherClass, ClassEnrollment, TeacherContent, TeacherQuiz, QuizAttempt


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


# Teacher Models Admin

@admin.register(TeacherClass)
class TeacherClassAdmin(admin.ModelAdmin):
    list_display = ['name', 'teacher', 'subject', 'grade_level', 'get_student_count', 'invitation_code', 'is_active', 'created_at']
    list_filter = ['subject', 'grade_level', 'is_active', 'created_at']
    search_fields = ['name', 'teacher__user__username', 'subject', 'invitation_code']
    readonly_fields = ['invitation_code', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Class Information', {
            'fields': ('teacher', 'name', 'subject', 'grade_level', 'description')
        }),
        ('Settings', {
            'fields': ('max_students', 'is_active', 'invitation_code')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('teacher__user')


@admin.register(ClassEnrollment)
class ClassEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'teacher_class', 'enrolled_at', 'is_active']
    list_filter = ['is_active', 'enrolled_at', 'teacher_class__subject']
    search_fields = ['student__user__username', 'teacher_class__name', 'teacher_class__teacher__user__username']
    readonly_fields = ['enrolled_at']
    
    fieldsets = (
        ('Enrollment Information', {
            'fields': ('teacher_class', 'student', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('enrolled_at',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student__user', 'teacher_class__teacher__user')


@admin.register(TeacherContent)
class TeacherContentAdmin(admin.ModelAdmin):
    list_display = ['title', 'teacher', 'subject', 'grade_level', 'is_public', 'created_at']
    list_filter = ['subject', 'grade_level', 'is_public', 'created_at']
    search_fields = ['title', 'teacher__user__username', 'subject', 'description']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['assigned_classes']
    
    fieldsets = (
        ('Content Information', {
            'fields': ('teacher', 'uploaded_content', 'title', 'description')
        }),
        ('Classification', {
            'fields': ('subject', 'grade_level', 'is_public')
        }),
        ('Class Assignment', {
            'fields': ('assigned_classes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('teacher__user', 'uploaded_content')


@admin.register(TeacherQuiz)
class TeacherQuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'teacher', 'get_question_count', 'time_limit_minutes', 'attempts_allowed', 'is_active', 'due_date']
    list_filter = ['is_active', 'attempts_allowed', 'created_at', 'due_date']
    search_fields = ['title', 'teacher__user__username', 'instructions']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['assigned_classes']
    
    fieldsets = (
        ('Quiz Information', {
            'fields': ('teacher', 'generated_quiz', 'title', 'instructions')
        }),
        ('Quiz Settings', {
            'fields': ('time_limit_minutes', 'attempts_allowed', 'is_active', 'due_date')
        }),
        ('Questions', {
            'fields': ('customized_questions',),
            'classes': ('collapse',)
        }),
        ('Class Assignment', {
            'fields': ('assigned_classes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('teacher__user', 'generated_quiz')


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['student', 'quiz', 'attempt_number', 'score', 'time_taken_minutes', 'completed_at']
    list_filter = ['attempt_number', 'completed_at', 'quiz__title']
    search_fields = ['student__user__username', 'quiz__title', 'quiz__teacher__user__username']
    readonly_fields = ['started_at', 'completed_at']
    
    fieldsets = (
        ('Attempt Information', {
            'fields': ('quiz', 'student', 'attempt_number')
        }),
        ('Performance', {
            'fields': ('score', 'time_taken_minutes', 'answers'),
            'classes': ('collapse',)
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at')
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student__user', 'quiz__teacher__user')