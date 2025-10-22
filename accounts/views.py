from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import requires_csrf_token
from django.db import transaction
from metlab_edu.rate_limiting import login_rate_limit
import logging

logger = logging.getLogger(__name__)
from .models import User, StudentProfile, TeacherProfile, ParentProfile
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from .decorators import student_required, teacher_required, parent_required, profile_required


def register_view(request):
    """User registration view with role-based profile creation"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save(commit=False)
                    user.is_active = False  # User needs to verify email first
                    user.save()
                    
                    # Create role-specific profile
                    role = user.role
                    if role == 'student':
                        StudentProfile.objects.create(user=user)
                    elif role == 'teacher':
                        TeacherProfile.objects.create(
                            user=user,
                            institution=form.cleaned_data.get('institution', '')
                        )
                    elif role == 'parent':
                        ParentProfile.objects.create(user=user)
                    
                    # Send verification email (skip if email backend not configured)
                    try:
                        send_verification_email(request, user)
                    except Exception as email_error:
                        logger.warning(f"Email verification failed for user {user.username}: {email_error}")
                        # Don't fail registration if email fails
                        user.is_active = True  # Activate user if email fails
                        user.email_verified = True
                        user.save()
                    
                    messages.success(
                        request, 
                        'Registration successful! Please check your email to verify your account.' if not user.is_active else 'Registration successful! You can now log in.'
                    )
                    return redirect('accounts:login')
                    
            except Exception as e:
                logger.error(f"Registration failed for user data {form.cleaned_data}: {e}")
                messages.error(request, f'Registration failed: {str(e)}. Please try again.')
        else:
            # Form is not valid, show form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
                
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


@login_rate_limit(rate='5/m')  # 5 login attempts per minute
def login_view(request):
    """Custom login view with role-based redirect"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                if not user.email_verified:
                    messages.error(
                        request, 
                        'Please verify your email address before logging in.'
                    )
                    return render(request, 'accounts/login.html', {'form': form})
                
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                
                # Role-based redirect
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                
                return redirect('accounts:dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('accounts:login')


def send_verification_email(request, user):
    """Send email verification link to user"""
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    verification_link = request.build_absolute_uri(
        reverse('accounts:verify_email', kwargs={'uidb64': uid, 'token': token})
    )
    
    subject = 'Verify your Metlab.edu account'
    message = render_to_string('accounts/verification_email.html', {
        'user': user,
        'verification_link': verification_link,
    })
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=message,
            fail_silently=False,
        )
    except Exception as e:
        # In development, we'll just print the verification link
        print(f"Verification link for {user.email}: {verification_link}")


def verify_email(request, uidb64, token):
    """Email verification view"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        user.email_verified = True
        user.is_active = True
        user.save()
        
        messages.success(
            request, 
            'Your email has been verified successfully! You can now log in.'
        )
        return redirect('login')
    else:
        messages.error(
            request, 
            'The verification link is invalid or has expired.'
        )
        return redirect('register')


@login_required
def dashboard_view(request):
    """Role-based dashboard redirect"""
    user = request.user
    
    if user.role == 'student':
        return redirect('accounts:student_dashboard')
    elif user.role == 'teacher':
        return redirect('accounts:teacher_dashboard')
    elif user.role == 'parent':
        return redirect('accounts:parent_dashboard')
    else:
        messages.error(request, 'Invalid user role.')
        return redirect('accounts:login')


@student_required
@profile_required
def student_dashboard(request):
    """Enhanced student dashboard view with daily lessons, progress, and recommendations"""
    from learning.models import DailyLesson, LearningSession, WeaknessAnalysis, PersonalizedRecommendation
    from learning.services import DailyLessonService, WeaknessAnalysisService, RecommendationService
    from django.utils import timezone
    from datetime import timedelta
    
    student_profile = request.user.student_profile
    
    # Get or generate today's lesson
    today_lesson = DailyLessonService.get_student_daily_lesson(student_profile)
    
    # Calculate daily progress percentage
    daily_progress_percentage = 0
    if today_lesson:
        if today_lesson.status == 'completed':
            daily_progress_percentage = 100
        elif today_lesson.status == 'active':
            daily_progress_percentage = 50
        else:
            daily_progress_percentage = 0
    
    # Get recent learning sessions
    recent_sessions = LearningSession.objects.filter(
        student=student_profile,
        status='completed'
    ).order_by('-start_time')[:5]
    
    # Get top weaknesses for reminders
    weak_topics = WeaknessAnalysisService.get_student_weaknesses(student_profile, limit=3)
    
    # Get active recommendations
    recommendations = RecommendationService.get_active_recommendations(student_profile, limit=3)
    
    # Generate new recommendations if none exist
    if not recommendations.exists():
        try:
            RecommendationService.generate_weakness_recommendations(student_profile)
            RecommendationService.generate_content_recommendations(student_profile)
            recommendations = RecommendationService.get_active_recommendations(student_profile, limit=3)
        except Exception as e:
            # Handle any errors in recommendation generation
            print(f"Error generating recommendations: {e}")
            recommendations = []
    
    # Get achievement data
    from gamification.services import AchievementService
    from gamification.models import VirtualCurrency
    
    # Get recent achievements
    recent_achievements = AchievementService.get_recent_achievements(student_profile, days=7)[:3]
    
    # Get achievement statistics
    achievement_stats = AchievementService.get_achievement_stats(student_profile)
    
    # Get virtual currency
    try:
        virtual_currency = VirtualCurrency.objects.get(student=student_profile)
    except VirtualCurrency.DoesNotExist:
        virtual_currency = None
    
    context = {
        'user': request.user,
        'profile': student_profile,
        'page_title': 'Student Dashboard',
        'today_lesson': today_lesson,
        'daily_progress_percentage': daily_progress_percentage,
        'recent_sessions': recent_sessions,
        'weak_topics': weak_topics,
        'recommendations': recommendations,
        'recent_achievements': recent_achievements,
        'achievement_stats': achievement_stats,
        'virtual_currency': virtual_currency,
    }
    return render(request, 'accounts/student_dashboard.html', context)


@teacher_required
@profile_required
def teacher_dashboard(request):
    """Teacher dashboard view"""
    teacher_profile = request.user.teacher_profile
    context = {
        'user': request.user,
        'profile': teacher_profile,
        'page_title': 'Teacher Dashboard'
    }
    return render(request, 'accounts/teacher_dashboard.html', context)


@parent_required
@profile_required
def parent_dashboard(request):
    """Parent dashboard view - redirect to learning parent dashboard"""
    return redirect('learning:parent_dashboard')

@requires_csrf_token
def csrf_failure(request, reason=""):
    """
    Custom CSRF failure view to handle CSRF token failures gracefully
    """
    logger.warning(f"CSRF failure for user {request.user}: {reason}")
    
    # Check if request is AJAX (modern way)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': 'CSRF token missing or incorrect. Please refresh the page and try again.',
            'code': 'CSRF_FAILURE'
        }, status=403)
    
    return render(request, 'accounts/csrf_failure.html', {
        'reason': reason,
        'title': 'Security Error'
    }, status=403)