from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator
from django.db import transaction
from django.utils import timezone
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Avg, Count, Sum
from datetime import datetime, timedelta
import json
import logging

from accounts.decorators import parent_required
from accounts.models import ParentProfile, StudentProfile
from .models import LearningSession, DailyLesson, WeaknessAnalysis, PersonalizedRecommendation
from gamification.models import StudentAchievement, VirtualCurrency

logger = logging.getLogger(__name__)


@login_required
@parent_required
def parent_dashboard(request):
    """Main dashboard for parent monitoring"""
    parent_profile = request.user.parent_profile
    
    # Get all children
    children = parent_profile.children.all()
    
    # Get screen time limits from parent profile
    screen_time_limits = parent_profile.screen_time_limits
    
    # Prepare data for each child
    children_data = []
    for child in children:
        # Get recent learning sessions (last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        recent_sessions = LearningSession.objects.filter(
            student=child,
            start_time__gte=week_ago,
            status='completed'
        )
        
        # Calculate weekly stats
        total_time_minutes = recent_sessions.aggregate(
            total=Sum('time_spent_minutes')
        )['total'] or 0
        
        avg_performance = recent_sessions.aggregate(
            avg=Avg('performance_score')
        )['avg'] or 0
        
        # Get current streak
        current_streak = child.current_streak
        
        # Get recent achievements (last 7 days)
        recent_achievements = StudentAchievement.objects.filter(
            student=child,
            earned_at__gte=week_ago
        ).count()
        
        # Get current weaknesses
        current_weaknesses = WeaknessAnalysis.objects.filter(
            student=child,
            weakness_level__in=['high', 'critical']
        ).count()
        
        # Get today's lesson status
        today = timezone.now().date()
        today_lesson = DailyLesson.objects.filter(
            student=child,
            lesson_date=today
        ).first()
        
        # Get screen time limit for this child
        child_screen_limit = screen_time_limits.get(str(child.id), {})
        daily_limit_minutes = child_screen_limit.get('daily_limit_minutes', 60)  # Default 1 hour
        
        # Calculate today's screen time
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_sessions = LearningSession.objects.filter(
            student=child,
            start_time__gte=today_start,
            status='completed'
        )
        today_screen_time = today_sessions.aggregate(
            total=Sum('time_spent_minutes')
        )['total'] or 0
        
        children_data.append({
            'child': child,
            'weekly_time_minutes': total_time_minutes,
            'avg_performance': round(avg_performance, 1),
            'current_streak': current_streak,
            'recent_achievements': recent_achievements,
            'current_weaknesses': current_weaknesses,
            'today_lesson': today_lesson,
            'daily_limit_minutes': daily_limit_minutes,
            'today_screen_time': today_screen_time,
            'screen_time_percentage': min(100, (today_screen_time / daily_limit_minutes * 100)) if daily_limit_minutes > 0 else 0,
        })
    
    context = {
        'parent_profile': parent_profile,
        'children_data': children_data,
        'total_children': len(children),
    }
    
    return render(request, 'learning/parent_dashboard.html', context)


@login_required
@parent_required
def child_progress_detail(request, child_id):
    """Detailed progress view for a specific child"""
    parent_profile = request.user.parent_profile
    child = get_object_or_404(
        StudentProfile,
        id=child_id,
        parents=parent_profile
    )
    
    # Get time period from query params (default: last 30 days)
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Get learning sessions for the period
    sessions = LearningSession.objects.filter(
        student=child,
        start_time__gte=start_date,
        status='completed'
    ).order_by('-start_time')
    
    # Calculate performance trends
    daily_performance = {}
    daily_time = {}
    
    for session in sessions:
        date_key = session.start_time.date()
        if date_key not in daily_performance:
            daily_performance[date_key] = []
            daily_time[date_key] = 0
        
        daily_performance[date_key].append(session.performance_score or 0)
        daily_time[date_key] += session.time_spent_minutes
    
    # Calculate averages
    performance_trend = []
    time_trend = []
    
    for date in sorted(daily_performance.keys()):
        avg_performance = sum(daily_performance[date]) / len(daily_performance[date])
        performance_trend.append({
            'date': date.strftime('%Y-%m-%d'),
            'performance': round(avg_performance, 1)
        })
        time_trend.append({
            'date': date.strftime('%Y-%m-%d'),
            'time_minutes': daily_time[date]
        })
    
    # Get weaknesses
    weaknesses = WeaknessAnalysis.objects.filter(
        student=child
    ).order_by('-priority_level', '-weakness_score')
    
    # Get recent achievements
    recent_achievements = StudentAchievement.objects.filter(
        student=child,
        earned_at__gte=start_date
    ).select_related('achievement').order_by('-earned_at')
    
    # Get daily lessons completion rate
    daily_lessons = DailyLesson.objects.filter(
        student=child,
        lesson_date__gte=start_date.date()
    )
    
    completed_lessons = daily_lessons.filter(status='completed').count()
    total_lessons = daily_lessons.count()
    completion_rate = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
    
    # Get recommendations
    active_recommendations = PersonalizedRecommendation.objects.filter(
        student=child,
        status__in=['pending', 'viewed']
    ).order_by('-priority', '-created_at')
    
    context = {
        'parent_profile': parent_profile,
        'child': child,
        'days': days,
        'sessions': sessions[:10],  # Last 10 sessions
        'performance_trend': performance_trend,
        'time_trend': time_trend,
        'weaknesses': weaknesses,
        'recent_achievements': recent_achievements[:5],
        'completion_rate': round(completion_rate, 1),
        'active_recommendations': active_recommendations[:5],
        'total_sessions': sessions.count(),
        'avg_performance': sessions.aggregate(avg=Avg('performance_score'))['avg'] or 0,
        'total_time': sessions.aggregate(total=Sum('time_spent_minutes'))['total'] or 0,
    }
    
    return render(request, 'learning/child_progress_detail.html', context)


@login_required
@parent_required
def screen_time_settings(request, child_id):
    """Screen time limit settings for a specific child"""
    parent_profile = request.user.parent_profile
    child = get_object_or_404(
        StudentProfile,
        id=child_id,
        parents=parent_profile
    )
    
    if request.method == 'POST':
        try:
            # Get form data
            daily_limit_minutes = int(request.POST.get('daily_limit_minutes', 60))
            weekly_limit_minutes = int(request.POST.get('weekly_limit_minutes', 420))  # 7 hours
            break_reminder_minutes = int(request.POST.get('break_reminder_minutes', 30))
            bedtime_hour = int(request.POST.get('bedtime_hour', 21))  # 9 PM
            wakeup_hour = int(request.POST.get('wakeup_hour', 7))   # 7 AM
            weekend_extra_minutes = int(request.POST.get('weekend_extra_minutes', 30))
            
            # Validate inputs
            if daily_limit_minutes < 15 or daily_limit_minutes > 480:  # 15 min to 8 hours
                raise ValueError("Daily limit must be between 15 minutes and 8 hours")
            
            if weekly_limit_minutes < daily_limit_minutes:
                raise ValueError("Weekly limit cannot be less than daily limit")
            
            # Update screen time limits
            screen_time_limits = parent_profile.screen_time_limits.copy()
            screen_time_limits[str(child.id)] = {
                'daily_limit_minutes': daily_limit_minutes,
                'weekly_limit_minutes': weekly_limit_minutes,
                'break_reminder_minutes': break_reminder_minutes,
                'bedtime_hour': bedtime_hour,
                'wakeup_hour': wakeup_hour,
                'weekend_extra_minutes': weekend_extra_minutes,
                'updated_at': timezone.now().isoformat(),
            }
            
            parent_profile.screen_time_limits = screen_time_limits
            parent_profile.save()
            
            messages.success(request, f'Screen time settings updated for {child.user.username}')
            return redirect('learning:parent_dashboard')
            
        except (ValueError, TypeError) as e:
            messages.error(request, f'Invalid input: {str(e)}')
    
    # Get current settings
    current_settings = parent_profile.screen_time_limits.get(str(child.id), {})
    
    context = {
        'parent_profile': parent_profile,
        'child': child,
        'current_settings': current_settings,
        'default_settings': {
            'daily_limit_minutes': 60,
            'weekly_limit_minutes': 420,
            'break_reminder_minutes': 30,
            'bedtime_hour': 21,
            'wakeup_hour': 7,
            'weekend_extra_minutes': 30,
        }
    }
    
    return render(request, 'learning/screen_time_settings.html', context)


@login_required
@parent_required
def notification_settings(request):
    """Parent notification preferences"""
    parent_profile = request.user.parent_profile
    
    if request.method == 'POST':
        try:
            # Get notification preferences
            preferences = {
                'daily_progress_summary': request.POST.get('daily_progress_summary') == 'on',
                'weekly_report': request.POST.get('weekly_report') == 'on',
                'achievement_notifications': request.POST.get('achievement_notifications') == 'on',
                'weakness_alerts': request.POST.get('weakness_alerts') == 'on',
                'screen_time_alerts': request.POST.get('screen_time_alerts') == 'on',
                'missed_lesson_alerts': request.POST.get('missed_lesson_alerts') == 'on',
                'performance_concerns': request.POST.get('performance_concerns') == 'on',
                'email_notifications': request.POST.get('email_notifications') == 'on',
                'sms_notifications': request.POST.get('sms_notifications') == 'on',
                'updated_at': timezone.now().isoformat(),
            }
            
            parent_profile.notification_preferences = preferences
            parent_profile.save()
            
            messages.success(request, 'Notification settings updated successfully')
            return redirect('learning:parent_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error updating settings: {str(e)}')
    
    context = {
        'parent_profile': parent_profile,
        'current_preferences': parent_profile.notification_preferences,
    }
    
    return render(request, 'learning/notification_settings.html', context)


@login_required
@parent_required
def link_child_account(request):
    """Link a child's account to parent profile"""
    parent_profile = request.user.parent_profile
    
    if request.method == 'POST':
        child_username = request.POST.get('child_username', '').strip()
        link_code = request.POST.get('link_code', '').strip()
        
        if not child_username or not link_code:
            messages.error(request, 'Both username and link code are required')
            return redirect('learning:link_child_account')
        
        try:
            # Find the student profile
            child_profile = StudentProfile.objects.select_related('user').get(
                user__username=child_username
            )
            
            # Verify link code (this would be generated by the student)
            # For now, we'll use a simple format: "PARENT_" + child_id
            expected_code = f"PARENT_{child_profile.id}"
            
            if link_code.upper() != expected_code:
                messages.error(request, 'Invalid link code. Please check with your child.')
                return redirect('learning:link_child_account')
            
            # Check if already linked
            if parent_profile.children.filter(id=child_profile.id).exists():
                messages.warning(request, f'{child_username} is already linked to your account')
                return redirect('learning:parent_dashboard')
            
            # Link the accounts
            parent_profile.children.add(child_profile)
            
            messages.success(request, f'Successfully linked {child_username} to your account')
            return redirect('learning:parent_dashboard')
            
        except StudentProfile.DoesNotExist:
            messages.error(request, f'Student account "{child_username}" not found')
        except Exception as e:
            messages.error(request, f'Error linking account: {str(e)}')
    
    context = {
        'parent_profile': parent_profile,
    }
    
    return render(request, 'learning/link_child_account.html', context)


@login_required
@parent_required
@require_http_methods(["POST"])
def unlink_child_account(request, child_id):
    """Unlink a child's account from parent profile"""
    parent_profile = request.user.parent_profile
    
    try:
        child = get_object_or_404(
            StudentProfile,
            id=child_id,
            parents=parent_profile
        )
        
        parent_profile.children.remove(child)
        messages.success(request, f'Successfully unlinked {child.user.username} from your account')
        
    except Exception as e:
        messages.error(request, f'Error unlinking account: {str(e)}')
    
    return redirect('learning:parent_dashboard')


# AJAX endpoints

@login_required
@parent_required
def get_child_screen_time(request, child_id):
    """AJAX endpoint to get current screen time for a child"""
    parent_profile = request.user.parent_profile
    
    try:
        child = get_object_or_404(
            StudentProfile,
            id=child_id,
            parents=parent_profile
        )
        
        # Get today's screen time
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_sessions = LearningSession.objects.filter(
            student=child,
            start_time__gte=today_start,
            status='completed'
        )
        
        today_screen_time = today_sessions.aggregate(
            total=Sum('time_spent_minutes')
        )['total'] or 0
        
        # Get screen time limit
        screen_time_limits = parent_profile.screen_time_limits
        child_limit = screen_time_limits.get(str(child.id), {})
        daily_limit = child_limit.get('daily_limit_minutes', 60)
        
        return JsonResponse({
            'success': True,
            'today_screen_time': today_screen_time,
            'daily_limit': daily_limit,
            'percentage': min(100, (today_screen_time / daily_limit * 100)) if daily_limit > 0 else 0,
            'remaining_minutes': max(0, daily_limit - today_screen_time),
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@parent_required
def get_child_performance_data(request, child_id):
    """AJAX endpoint to get performance data for charts"""
    parent_profile = request.user.parent_profile
    
    try:
        child = get_object_or_404(
            StudentProfile,
            id=child_id,
            parents=parent_profile
        )
        
        days = int(request.GET.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        
        # Get daily performance data
        sessions = LearningSession.objects.filter(
            student=child,
            start_time__gte=start_date,
            status='completed'
        ).order_by('start_time')
        
        daily_data = {}
        for session in sessions:
            date_key = session.start_time.date().strftime('%Y-%m-%d')
            if date_key not in daily_data:
                daily_data[date_key] = {
                    'performance_scores': [],
                    'time_minutes': 0,
                    'sessions': 0
                }
            
            daily_data[date_key]['performance_scores'].append(session.performance_score or 0)
            daily_data[date_key]['time_minutes'] += session.time_spent_minutes
            daily_data[date_key]['sessions'] += 1
        
        # Format for chart
        chart_data = []
        for date_str in sorted(daily_data.keys()):
            data = daily_data[date_str]
            avg_performance = sum(data['performance_scores']) / len(data['performance_scores'])
            
            chart_data.append({
                'date': date_str,
                'performance': round(avg_performance, 1),
                'time_minutes': data['time_minutes'],
                'sessions': data['sessions']
            })
        
        return JsonResponse({
            'success': True,
            'data': chart_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@parent_required
def send_encouragement_message(request, child_id):
    """Send an encouragement message to a child"""
    parent_profile = request.user.parent_profile
    
    if request.method == 'POST':
        try:
            child = get_object_or_404(
                StudentProfile,
                id=child_id,
                parents=parent_profile
            )
            
            message_text = request.POST.get('message', '').strip()
            if not message_text:
                return JsonResponse({
                    'success': False,
                    'error': 'Message cannot be empty'
                })
            
            # Create a personalized recommendation with the encouragement message
            PersonalizedRecommendation.objects.create(
                student=child,
                recommendation_type='encouragement',
                title='Message from Parent',
                description=message_text,
                content={'type': 'parent_message', 'sender': parent_profile.user.username},
                priority=3,
                estimated_time_minutes=1
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Encouragement message sent successfully!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })