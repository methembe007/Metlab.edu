from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
from django.db.models import Count, Avg, Sum
from django.contrib import messages
import json

from .models import LearningSession, WeaknessAnalysis, PersonalizedRecommendation, DailyLesson, LessonProgress
from .services import LearningSessionService, WeaknessAnalysisService, RecommendationService, DailyLessonService
from .lesson_service import LessonDeliveryService
from accounts.models import StudentProfile
from content.models import UploadedContent


@method_decorator(login_required, name='dispatch')
class SessionTrackingView(View):
    """API view for learning session tracking"""
    
    def post(self, request):
        """Start a new learning session"""
        try:
            data = json.loads(request.body)
            content_id = data.get('content_id')
            session_type = data.get('session_type', 'mixed')
            difficulty_level = data.get('difficulty_level', 'intermediate')
            
            # Get student profile
            student_profile = get_object_or_404(StudentProfile, user=request.user)
            content = get_object_or_404(UploadedContent, id=content_id)
            
            # Start new session
            session = LearningSessionService.start_session(
                student_profile=student_profile,
                content=content,
                session_type=session_type,
                difficulty_level=difficulty_level
            )
            
            return JsonResponse({
                'success': True,
                'session_id': session.id,
                'message': 'Learning session started successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    def put(self, request, session_id):
        """Update session progress"""
        try:
            data = json.loads(request.body)
            questions_attempted = data.get('questions_attempted', 0)
            questions_correct = data.get('questions_correct', 0)
            concepts_covered = data.get('concepts_covered', [])
            
            session = LearningSessionService.update_session_progress(
                session_id=session_id,
                questions_attempted=questions_attempted,
                questions_correct=questions_correct,
                concepts_covered=concepts_covered
            )
            
            if session:
                return JsonResponse({
                    'success': True,
                    'performance_score': session.performance_score,
                    'message': 'Session updated successfully'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Session not found or not active'
                }, status=404)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    def delete(self, request, session_id):
        """Complete a learning session"""
        try:
            data = json.loads(request.body) if request.body else {}
            xp_earned = data.get('xp_earned', 0)
            
            session = LearningSessionService.complete_session(
                session_id=session_id,
                xp_earned=xp_earned
            )
            
            if session:
                return JsonResponse({
                    'success': True,
                    'final_score': session.performance_score,
                    'time_spent': session.time_spent_minutes,
                    'xp_earned': session.xp_earned,
                    'message': 'Session completed successfully'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Session not found'
                }, status=404)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


@login_required
def student_analytics_view(request):
    """View for displaying student analytics"""
    try:
        student_profile = get_object_or_404(StudentProfile, user=request.user)
        
        # Get session statistics
        stats = LearningSessionService.get_session_statistics(student_profile)
        
        # Get recent sessions
        recent_sessions = LearningSessionService.get_student_sessions(student_profile, limit=5)
        
        # Get weaknesses
        weaknesses = WeaknessAnalysisService.get_student_weaknesses(student_profile, limit=5)
        
        # Get recommendations
        recommendations = RecommendationService.get_active_recommendations(student_profile, limit=3)
        
        # Get advanced analytics
        from .analytics import PerformanceAnalyticsEngine
        learning_patterns = PerformanceAnalyticsEngine.analyze_learning_patterns(student_profile)
        
        # Get performance data for charts
        performance_data = get_performance_chart_data(student_profile)
        subject_data = get_subject_distribution_data(student_profile)
        weekly_progress = get_weekly_progress_data(student_profile)
        
        context = {
            'stats': stats,
            'recent_sessions': recent_sessions,
            'weaknesses': weaknesses,
            'recommendations': recommendations,
            'learning_patterns': learning_patterns,
            'performance_data': performance_data,
            'subject_data': subject_data,
            'weekly_progress': weekly_progress,
        }
        
        return render(request, 'learning/analytics.html', context)
        
    except StudentProfile.DoesNotExist:
        return render(request, 'learning/no_profile.html')


def get_performance_chart_data(student_profile):
    """Get performance data for line chart"""
    from datetime import timedelta
    
    sessions = LearningSession.objects.filter(
        student=student_profile,
        status='completed',
        performance_score__isnull=False
    ).order_by('start_time')[:20]  # Last 20 sessions
    
    data = {
        'labels': [],
        'scores': [],
        'dates': []
    }
    
    for i, session in enumerate(sessions):
        data['labels'].append(f"Session {i+1}")
        data['scores'].append(session.performance_score)
        data['dates'].append(session.start_time.strftime('%Y-%m-%d'))
    
    return data


def get_subject_distribution_data(student_profile):
    """Get subject distribution data for pie chart"""
    from django.db.models import Sum
    
    subject_data = LearningSession.objects.filter(
        student=student_profile,
        status='completed'
    ).values('content__subject').annotate(
        total_time=Sum('time_spent_minutes'),
        session_count=Count('id')
    ).order_by('-total_time')
    
    data = {
        'labels': [],
        'time_data': [],
        'session_data': []
    }
    
    for item in subject_data:
        subject = item['content__subject'] or 'General'
        data['labels'].append(subject)
        data['time_data'].append(item['total_time'] or 0)
        data['session_data'].append(item['session_count'])
    
    return data


def get_weekly_progress_data(student_profile):
    """Get weekly progress data for bar chart"""
    from datetime import timedelta
    from django.db.models.functions import TruncWeek
    
    cutoff_date = timezone.now() - timedelta(weeks=8)
    
    weekly_data = LearningSession.objects.filter(
        student=student_profile,
        start_time__gte=cutoff_date,
        status='completed'
    ).annotate(
        week=TruncWeek('start_time')
    ).values('week').annotate(
        session_count=Count('id'),
        total_time=Sum('time_spent_minutes'),
        avg_performance=Avg('performance_score')
    ).order_by('week')
    
    data = {
        'labels': [],
        'sessions': [],
        'time': [],
        'performance': []
    }
    
    for item in weekly_data:
        week_str = item['week'].strftime('%b %d')
        data['labels'].append(week_str)
        data['sessions'].append(item['session_count'])
        data['time'].append(item['total_time'] or 0)
        data['performance'].append(round(item['avg_performance'] or 0, 1))
    
    return data


@login_required
@require_http_methods(["GET"])
def get_recommendations(request):
    """API endpoint to get student recommendations"""
    try:
        student_profile = get_object_or_404(StudentProfile, user=request.user)
        
        # Generate new recommendations if needed
        RecommendationService.generate_weakness_recommendations(student_profile)
        RecommendationService.generate_content_recommendations(student_profile)
        
        # Get active recommendations
        recommendations = RecommendationService.get_active_recommendations(student_profile)
        
        recommendations_data = []
        for rec in recommendations:
            recommendations_data.append({
                'id': rec.id,
                'type': rec.recommendation_type,
                'title': rec.title,
                'description': rec.description,
                'priority': rec.priority,
                'estimated_time': rec.estimated_time_minutes,
                'status': rec.status,
                'created_at': rec.created_at.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'recommendations': recommendations_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def mark_recommendation_viewed(request, recommendation_id):
    """Mark a recommendation as viewed"""
    try:
        recommendation = RecommendationService.mark_recommendation_viewed(recommendation_id)
        
        if recommendation:
            return JsonResponse({
                'success': True,
                'message': 'Recommendation marked as viewed'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Recommendation not found'
            }, status=404)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def teacher_analytics_view(request):
    """Analytics view for teachers to monitor class performance"""
    try:
        from accounts.models import TeacherProfile
        teacher_profile = get_object_or_404(TeacherProfile, user=request.user)
        
        # Get students from teacher's uploaded content
        teacher_content = UploadedContent.objects.filter(user=request.user)
        student_sessions = LearningSession.objects.filter(
            content__in=teacher_content,
            status='completed'
        ).select_related('student', 'content')
        
        # Get class performance statistics
        class_stats = get_class_performance_stats(student_sessions)
        
        # Get top performing students
        top_students = get_top_performing_students(student_sessions)
        
        # Get content performance
        content_performance = get_content_performance_stats(teacher_content)
        
        # Get recent activity
        recent_activity = student_sessions.order_by('-start_time')[:10]
        
        context = {
            'class_stats': class_stats,
            'top_students': top_students,
            'content_performance': content_performance,
            'recent_activity': recent_activity,
            'teacher_content_count': teacher_content.count(),
        }
        
        return render(request, 'learning/teacher_analytics.html', context)
        
    except:
        return render(request, 'learning/no_teacher_profile.html')


@login_required
def parent_analytics_view(request):
    """Analytics view for parents to monitor their children's progress"""
    try:
        from accounts.models import ParentProfile
        parent_profile = get_object_or_404(ParentProfile, user=request.user)
        
        children_data = []
        for child in parent_profile.children.all():
            # Get child's statistics
            child_stats = LearningSessionService.get_session_statistics(child)
            
            # Get recent sessions
            recent_sessions = LearningSessionService.get_student_sessions(child, limit=3)
            
            # Get weaknesses
            weaknesses = WeaknessAnalysisService.get_student_weaknesses(child, limit=3)
            
            # Get learning patterns
            from .analytics import PerformanceAnalyticsEngine
            patterns = PerformanceAnalyticsEngine.analyze_learning_patterns(child, days=14)
            
            children_data.append({
                'profile': child,
                'stats': child_stats,
                'recent_sessions': recent_sessions,
                'weaknesses': weaknesses,
                'patterns': patterns
            })
        
        context = {
            'children_data': children_data,
            'total_children': len(children_data)
        }
        
        return render(request, 'learning/parent_analytics.html', context)
        
    except:
        return render(request, 'learning/no_parent_profile.html')


def get_class_performance_stats(student_sessions):
    """Calculate class performance statistics"""
    if not student_sessions.exists():
        return {
            'total_students': 0,
            'total_sessions': 0,
            'avg_performance': 0,
            'total_study_time': 0,
            'active_students_week': 0
        }
    
    from datetime import timedelta
    week_ago = timezone.now() - timedelta(days=7)
    
    stats = student_sessions.aggregate(
        total_sessions=Count('id'),
        avg_performance=Avg('performance_score'),
        total_study_time=Sum('time_spent_minutes')
    )
    
    total_students = student_sessions.values('student').distinct().count()
    active_students_week = student_sessions.filter(
        start_time__gte=week_ago
    ).values('student').distinct().count()
    
    return {
        'total_students': total_students,
        'total_sessions': stats['total_sessions'] or 0,
        'avg_performance': round(stats['avg_performance'] or 0, 1),
        'total_study_time': stats['total_study_time'] or 0,
        'active_students_week': active_students_week
    }


def get_top_performing_students(student_sessions):
    """Get top performing students"""
    student_performance = student_sessions.values(
        'student__user__username',
        'student__user__first_name',
        'student__user__last_name'
    ).annotate(
        avg_performance=Avg('performance_score'),
        total_sessions=Count('id'),
        total_time=Sum('time_spent_minutes')
    ).filter(
        total_sessions__gte=3  # At least 3 sessions
    ).order_by('-avg_performance')[:5]
    
    return student_performance


def get_content_performance_stats(teacher_content):
    """Get performance statistics for teacher's content"""
    content_stats = []
    
    for content in teacher_content:
        sessions = LearningSession.objects.filter(
            content=content,
            status='completed'
        )
        
        if sessions.exists():
            stats = sessions.aggregate(
                avg_performance=Avg('performance_score'),
                total_sessions=Count('id'),
                unique_students=Count('student', distinct=True)
            )
            
            content_stats.append({
                'content': content,
                'avg_performance': round(stats['avg_performance'] or 0, 1),
                'total_sessions': stats['total_sessions'],
                'unique_students': stats['unique_students']
            })
    
    # Sort by average performance
    content_stats.sort(key=lambda x: x['avg_performance'], reverse=True)
    return content_stats[:10]  # Top 10


@login_required
def daily_lesson_view(request):
    """View for displaying and managing daily lessons"""
    try:
        student_profile = get_object_or_404(StudentProfile, user=request.user)
        
        # Get or generate today's lesson
        today_lesson = DailyLessonService.get_student_daily_lesson(student_profile)
        
        # Get recent completed lessons for progress tracking
        recent_lessons = DailyLesson.objects.filter(
            student=student_profile,
            status='completed'
        ).order_by('-lesson_date')[:5]
        
        # Calculate streak information
        streak_info = calculate_lesson_streak(student_profile)
        
        context = {
            'today_lesson': today_lesson,
            'recent_lessons': recent_lessons,
            'streak_info': streak_info,
        }
        
        return render(request, 'learning/daily_lesson.html', context)
        
    except StudentProfile.DoesNotExist:
        return render(request, 'learning/no_profile.html')


@login_required
def lesson_detail_view(request, lesson_id):
    """View for displaying a specific lesson with activities"""
    try:
        student_profile = get_object_or_404(StudentProfile, user=request.user)
        lesson = get_object_or_404(DailyLesson, id=lesson_id, student=student_profile)
        
        # Get lesson progress if it exists
        progress_entries = LessonProgress.objects.filter(lesson=lesson).order_by('activity_index')
        
        context = {
            'lesson': lesson,
            'progress_entries': progress_entries,
            'activities': lesson.get_lesson_activities(),
            'materials': lesson.get_lesson_materials(),
        }
        
        return render(request, 'learning/lesson_detail.html', context)
        
    except (StudentProfile.DoesNotExist, DailyLesson.DoesNotExist):
        return render(request, 'learning/no_profile.html')


@login_required
@require_http_methods(["POST"])
def start_daily_lesson(request, lesson_id):
    """API endpoint to start a daily lesson"""
    try:
        student_profile = get_object_or_404(StudentProfile, user=request.user)
        lesson = get_object_or_404(DailyLesson, id=lesson_id, student=student_profile)
        
        if lesson.status == 'scheduled':
            lesson.start_lesson()
            
            return JsonResponse({
                'success': True,
                'message': 'Lesson started successfully',
                'lesson_id': lesson.id,
                'status': lesson.status
            })
        else:
            return JsonResponse({
                'success': False,
                'error': f'Lesson cannot be started. Current status: {lesson.status}'
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def complete_daily_lesson(request, lesson_id):
    """API endpoint to complete a daily lesson with enhanced validation and scoring"""
    try:
        data = json.loads(request.body)
        
        student_profile = get_object_or_404(StudentProfile, user=request.user)
        lesson = get_object_or_404(DailyLesson, id=lesson_id, student=student_profile)
        
        # Get all progress entries for validation
        progress_entries = LessonProgress.objects.filter(lesson=lesson)
        
        # Validate lesson completion
        is_valid, error_message = LessonDeliveryService.validate_lesson_completion(
            lesson, progress_entries
        )
        
        if not is_valid:
            return JsonResponse({
                'success': False,
                'error': f'Lesson validation failed: {error_message}'
            }, status=400)
        
        if lesson.status != 'active':
            return JsonResponse({
                'success': False,
                'error': f'Lesson cannot be completed. Current status: {lesson.status}'
            }, status=400)
        
        # Calculate performance score using the service
        calculated_score = LessonDeliveryService.calculate_lesson_score(lesson, progress_entries)
        
        # Use provided score or calculated score
        performance_score = data.get('performance_score', calculated_score)
        
        # Calculate completion ratio
        activities = lesson.get_lesson_activities()
        completion_ratio = len(progress_entries) / len(activities) if activities else 1.0
        
        # Calculate XP using the service
        calculated_xp = LessonDeliveryService.calculate_xp_earned(
            lesson, performance_score, completion_ratio
        )
        
        # Use provided XP or calculated XP
        xp_earned = data.get('xp_earned', calculated_xp)
        
        # Complete the lesson
        lesson.complete_lesson(performance_score=performance_score, xp_earned=xp_earned)
        
        # Check for new achievements after lesson completion
        from gamification.services import AchievementService, XPCalculationService, CoinRewardService, StreakService
        
        # Update streak
        StreakService.update_streak(lesson.student)
        
        # Award XP for lesson completion
        lesson_xp = XPCalculationService.calculate_lesson_xp(
            lesson.student, 
            lesson_score=performance_score,
            perfect_score=(performance_score == 100)
        )
        
        # Award coins for lesson completion
        lesson_coins = CoinRewardService.award_lesson_coins(
            lesson.student,
            perfect_score=(performance_score == 100)
        )
        
        # Check and award achievements
        new_achievements = AchievementService.check_and_award_achievements(lesson.student)
        
        response_data = {
            'success': True,
            'message': 'Lesson completed successfully',
            'performance_score': lesson.performance_score,
            'xp_earned': lesson.xp_earned,
            'time_spent': lesson.time_spent_minutes,
            'completion_ratio': completion_ratio,
            'activities_completed': len(progress_entries),
            'total_activities': len(activities),
            'bonus_xp': lesson_xp,
            'coins_earned': lesson_coins,
            'new_achievements': len(new_achievements),
            'current_streak': lesson.student.current_streak
        }
        
        return JsonResponse(response_data)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def record_lesson_progress(request, lesson_id):
    """API endpoint to record progress within a lesson"""
    try:
        data = json.loads(request.body)
        activity_index = data.get('activity_index')
        activity_type = data.get('activity_type')
        concept = data.get('concept', '')
        question_text = data.get('question_text', '')
        student_answer = data.get('student_answer', '')
        correct_answer = data.get('correct_answer', '')
        is_correct = data.get('is_correct')
        time_spent_seconds = data.get('time_spent_seconds', 0)
        difficulty_rating = data.get('difficulty_rating', '')
        
        student_profile = get_object_or_404(StudentProfile, user=request.user)
        lesson = get_object_or_404(DailyLesson, id=lesson_id, student=student_profile)
        
        # Create or update progress entry
        progress, created = LessonProgress.objects.update_or_create(
            lesson=lesson,
            activity_index=activity_index,
            defaults={
                'activity_type': activity_type,
                'concept': concept,
                'question_text': question_text,
                'student_answer': student_answer,
                'correct_answer': correct_answer,
                'is_correct': is_correct,
                'time_spent_seconds': time_spent_seconds,
                'difficulty_rating': difficulty_rating,
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Progress recorded successfully',
            'progress_id': progress.id,
            'created': created
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def skip_daily_lesson(request, lesson_id):
    """API endpoint to skip a daily lesson"""
    try:
        student_profile = get_object_or_404(StudentProfile, user=request.user)
        lesson = get_object_or_404(DailyLesson, id=lesson_id, student=student_profile)
        
        lesson.skip_lesson()
        
        return JsonResponse({
            'success': True,
            'message': 'Lesson skipped successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


def calculate_lesson_streak(student_profile):
    """Calculate lesson completion streak for a student"""
    from datetime import timedelta
    
    today = timezone.now().date()
    current_streak = 0
    longest_streak = 0
    temp_streak = 0
    
    # Get lessons from the past 30 days
    lessons = DailyLesson.objects.filter(
        student=student_profile,
        lesson_date__gte=today - timedelta(days=30)
    ).order_by('-lesson_date')
    
    # Calculate current streak (consecutive days from today backwards)
    for lesson in lessons:
        expected_date = today - timedelta(days=current_streak)
        if lesson.lesson_date == expected_date and lesson.status == 'completed':
            current_streak += 1
        else:
            break
    
    # Calculate longest streak
    for lesson in lessons:
        if lesson.status == 'completed':
            temp_streak += 1
            longest_streak = max(longest_streak, temp_streak)
        else:
            temp_streak = 0
    
    return {
        'current_streak': current_streak,
        'longest_streak': longest_streak,
        'total_completed': lessons.filter(status='completed').count(),
        'total_lessons': lessons.count()
    }


@login_required
def lesson_history_view(request):
    """View for displaying lesson history with filtering and pagination"""
    try:
        from django.core.paginator import Paginator
        student_profile = get_object_or_404(StudentProfile, user=request.user)
        
        # Get all lessons for the student
        lessons = DailyLesson.objects.filter(student=student_profile).order_by('-lesson_date')
        
        # Get comprehensive statistics using the lesson service
        stats = LessonDeliveryService.get_student_lesson_stats(student_profile)
        
        # Pagination
        paginator = Paginator(lessons, 10)  # Show 10 lessons per page
        page_number = request.GET.get('page')
        lessons_page = paginator.get_page(page_number)
        
        context = {
            'lessons': lessons_page,
            'stats': stats,
        }
        
        return render(request, 'learning/lesson_history.html', context)
        
    except StudentProfile.DoesNotExist:
        return render(request, 'learning/no_profile.html')


@login_required
@require_http_methods(["GET"])
def lesson_analytics_api(request, lesson_id):
    """API endpoint to get detailed analytics for a specific lesson"""
    try:
        student_profile = get_object_or_404(StudentProfile, user=request.user)
        lesson = get_object_or_404(DailyLesson, id=lesson_id, student=student_profile)
        
        # Use the lesson service to get comprehensive analytics
        analytics = LessonDeliveryService.get_lesson_analytics(lesson)
        
        return JsonResponse({
            'success': True,
            'analytics': analytics
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def practice_concept_view(request):
    """Simple practice view for concept-specific practice sessions"""
    try:
        student_profile = get_object_or_404(StudentProfile, user=request.user)
        concept = request.GET.get('concept', '')
        
        if concept:
            # Find content related to the concept
            from content.models import UploadedContent
            related_content = UploadedContent.objects.filter(
                key_concepts__icontains=concept,
                processing_status='completed'
            ).first()
            
            if related_content:
                # Redirect to content detail for practice
                return redirect('content:detail', content_id=related_content.id)
            else:
                messages.info(request, f'No practice content found for "{concept}". Try uploading relevant materials first.')
                return redirect('content:upload')
        else:
            messages.error(request, 'No concept specified for practice.')
            return redirect('accounts:student_dashboard')
            
    except StudentProfile.DoesNotExist:
        return render(request, 'learning/no_profile.html')