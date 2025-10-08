from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator
from django.db import transaction
from django.utils import timezone
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import logging

logger = logging.getLogger(__name__)

from accounts.decorators import teacher_required
from accounts.models import TeacherProfile, StudentProfile
from content.models import UploadedContent, GeneratedQuiz
from content.ai_services import ai_content_generator
from .teacher_models import TeacherClass, ClassEnrollment, TeacherContent, TeacherQuiz, QuizAttempt
from .teacher_forms import (
    TeacherClassForm, TeacherContentForm, TeacherQuizForm, 
    ClassEnrollmentForm, BulkContentDistributionForm, QuizCustomizationForm
)


@login_required
@teacher_required
def teacher_content_dashboard(request):
    """Main dashboard for teacher content management"""
    teacher_profile = request.user.teacher_profile
    
    # Get statistics
    total_classes = teacher_profile.classes.filter(is_active=True).count()
    total_students = ClassEnrollment.objects.filter(
        teacher_class__teacher=teacher_profile,
        is_active=True
    ).count()
    total_content = teacher_profile.teacher_content.count()
    total_quizzes = teacher_profile.teacher_quizzes.filter(is_active=True).count()
    
    # Get recent content
    recent_content = teacher_profile.teacher_content.all()[:5]
    
    # Get recent classes
    recent_classes = teacher_profile.classes.filter(is_active=True)[:5]
    
    context = {
        'teacher_profile': teacher_profile,
        'total_classes': total_classes,
        'total_students': total_students,
        'total_content': total_content,
        'total_quizzes': total_quizzes,
        'recent_content': recent_content,
        'recent_classes': recent_classes,
    }
    
    return render(request, 'learning/teacher_dashboard.html', context)


@login_required
@teacher_required
def upload_content(request):
    """Upload educational content for automatic quiz generation"""
    teacher_profile = request.user.teacher_profile
    
    if request.method == 'POST':
        form = TeacherContentForm(request.POST, request.FILES, teacher=teacher_profile)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create UploadedContent first
                    uploaded_content = UploadedContent.objects.create(
                        user=request.user,
                        file=form.cleaned_data['file']
                    )
                    
                    # Create TeacherContent
                    teacher_content = form.save(commit=False)
                    teacher_content.teacher = teacher_profile
                    teacher_content.uploaded_content = uploaded_content
                    teacher_content.save()
                    
                    # Save many-to-many relationships
                    form.save_m2m()
                    
                    # Start AI content generation
                    # Note: In production, this should be done asynchronously
                    try:
                        ai_content_generator.generate_all_content(uploaded_content)
                        uploaded_content.processing_status = 'completed'
                        uploaded_content.processed_at = timezone.now()
                        uploaded_content.save()
                    except Exception as e:
                        uploaded_content.processing_status = 'failed'
                        uploaded_content.save()
                        logger.error(f"Content processing failed: {str(e)}")
                    
                    messages.success(request, 'Content uploaded successfully! AI processing has started.')
                    return redirect('teacher_content_list')
            except Exception as e:
                messages.error(request, f'Error uploading content: {str(e)}')
    else:
        form = TeacherContentForm(teacher=teacher_profile)
    
    context = {
        'form': form,
        'teacher_profile': teacher_profile,
    }
    
    return render(request, 'learning/upload_content.html', context)


@login_required
@teacher_required
def content_list(request):
    """List all content uploaded by the teacher"""
    teacher_profile = request.user.teacher_profile
    
    content_list = teacher_profile.teacher_content.select_related('uploaded_content').all()
    
    # Pagination
    paginator = Paginator(content_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'teacher_profile': teacher_profile,
    }
    
    return render(request, 'learning/teacher_content_list.html', context)


@login_required
@teacher_required
def content_detail(request, content_id):
    """View details of uploaded content and generated materials"""
    teacher_profile = request.user.teacher_profile
    teacher_content = get_object_or_404(
        TeacherContent,
        id=content_id,
        teacher=teacher_profile
    )
    
    uploaded_content = teacher_content.uploaded_content
    
    # Get generated materials
    summaries = uploaded_content.summaries.all()
    quizzes = uploaded_content.quizzes.all()
    flashcards = uploaded_content.flashcards.all()
    
    context = {
        'teacher_content': teacher_content,
        'uploaded_content': uploaded_content,
        'summaries': summaries,
        'quizzes': quizzes,
        'flashcards': flashcards,
        'teacher_profile': teacher_profile,
    }
    
    return render(request, 'learning/teacher_content_detail.html', context)


@login_required
@teacher_required
def customize_quiz(request, quiz_id):
    """Customize an AI-generated quiz"""
    teacher_profile = request.user.teacher_profile
    generated_quiz = get_object_or_404(GeneratedQuiz, id=quiz_id)
    
    # Check if teacher has access to this quiz
    if not TeacherContent.objects.filter(
        teacher=teacher_profile,
        uploaded_content=generated_quiz.content
    ).exists():
        raise Http404("Quiz not found")
    
    # Check if teacher already has a customization for this quiz
    try:
        teacher_quiz = TeacherQuiz.objects.get(
            teacher=teacher_profile,
            generated_quiz=generated_quiz
        )
        is_editing = True
    except TeacherQuiz.DoesNotExist:
        teacher_quiz = None
        is_editing = False
    
    if request.method == 'POST':
        form = TeacherQuizForm(request.POST, instance=teacher_quiz, teacher=teacher_profile)
        if form.is_valid():
            teacher_quiz = form.save(commit=False)
            teacher_quiz.teacher = teacher_profile
            teacher_quiz.generated_quiz = generated_quiz
            
            # Get customized questions from the form
            questions_json = form.cleaned_data.get('questions_json')
            if questions_json:
                teacher_quiz.customized_questions = questions_json
            else:
                # Use original questions if no customization
                teacher_quiz.customized_questions = generated_quiz.questions
            
            teacher_quiz.save()
            form.save_m2m()
            
            messages.success(request, 'Quiz customized successfully!')
            return redirect('teacher_quiz_list')
    else:
        initial_data = {}
        if teacher_quiz:
            initial_data = {
                'title': teacher_quiz.title,
                'instructions': teacher_quiz.instructions,
                'time_limit_minutes': teacher_quiz.time_limit_minutes,
                'attempts_allowed': teacher_quiz.attempts_allowed,
                'due_date': teacher_quiz.due_date,
            }
        else:
            initial_data = {
                'title': generated_quiz.title,
                'attempts_allowed': 1,
            }
        
        form = TeacherQuizForm(initial=initial_data, teacher=teacher_profile)
    
    # Get questions for customization
    questions = teacher_quiz.customized_questions if teacher_quiz else generated_quiz.questions
    
    context = {
        'form': form,
        'generated_quiz': generated_quiz,
        'teacher_quiz': teacher_quiz,
        'questions': questions,
        'is_editing': is_editing,
        'teacher_profile': teacher_profile,
    }
    
    return render(request, 'learning/customize_quiz.html', context)


@login_required
@teacher_required
def quiz_list(request):
    """List all customized quizzes by the teacher"""
    teacher_profile = request.user.teacher_profile
    
    quiz_list = teacher_profile.teacher_quizzes.select_related('generated_quiz').all()
    
    # Pagination
    paginator = Paginator(quiz_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'teacher_profile': teacher_profile,
    }
    
    return render(request, 'learning/teacher_quiz_list.html', context)


@login_required
@teacher_required
def class_management(request):
    """Manage teacher classes"""
    teacher_profile = request.user.teacher_profile
    
    classes = teacher_profile.classes.all()
    
    context = {
        'classes': classes,
        'teacher_profile': teacher_profile,
    }
    
    return render(request, 'learning/class_management.html', context)


@login_required
@teacher_required
def create_class(request):
    """Create a new class"""
    teacher_profile = request.user.teacher_profile
    
    if request.method == 'POST':
        form = TeacherClassForm(request.POST)
        if form.is_valid():
            teacher_class = form.save(commit=False)
            teacher_class.teacher = teacher_profile
            teacher_class.save()
            
            messages.success(request, f'Class "{teacher_class.name}" created successfully! Invitation code: {teacher_class.invitation_code}')
            return redirect('class_management')
    else:
        form = TeacherClassForm()
    
    context = {
        'form': form,
        'teacher_profile': teacher_profile,
    }
    
    return render(request, 'learning/create_class.html', context)


@login_required
@teacher_required
def class_detail(request, class_id):
    """View class details and manage students"""
    teacher_profile = request.user.teacher_profile
    teacher_class = get_object_or_404(
        TeacherClass,
        id=class_id,
        teacher=teacher_profile
    )
    
    # Get enrolled students
    enrollments = teacher_class.enrollments.filter(is_active=True).select_related('student__user')
    
    # Get assigned content
    assigned_content = teacher_class.assigned_content.all()
    
    # Get assigned quizzes
    assigned_quizzes = teacher_class.assigned_quizzes.filter(is_active=True)
    
    context = {
        'teacher_class': teacher_class,
        'enrollments': enrollments,
        'assigned_content': assigned_content,
        'assigned_quizzes': assigned_quizzes,
        'teacher_profile': teacher_profile,
    }
    
    return render(request, 'learning/class_detail.html', context)


@login_required
@teacher_required
def bulk_content_distribution(request):
    """Distribute content to multiple classes"""
    teacher_profile = request.user.teacher_profile
    
    if request.method == 'POST':
        form = BulkContentDistributionForm(request.POST, teacher=teacher_profile)
        if form.is_valid():
            content_items = form.cleaned_data['content_items']
            target_classes = form.cleaned_data['target_classes']
            
            # Distribute content to classes
            for content_item in content_items:
                content_item.assigned_classes.add(*target_classes)
            
            messages.success(request, f'Successfully distributed {len(content_items)} content items to {len(target_classes)} classes.')
            return redirect('teacher_content_dashboard')
    else:
        form = BulkContentDistributionForm(teacher=teacher_profile)
    
    context = {
        'form': form,
        'teacher_profile': teacher_profile,
    }
    
    return render(request, 'learning/bulk_content_distribution.html', context)


@login_required
@teacher_required
def student_progress(request, class_id):
    """View student progress in a specific class"""
    teacher_profile = request.user.teacher_profile
    teacher_class = get_object_or_404(
        TeacherClass,
        id=class_id,
        teacher=teacher_profile
    )
    
    # Get enrolled students with their progress
    enrollments = teacher_class.enrollments.filter(is_active=True).select_related('student__user')
    
    student_progress = []
    for enrollment in enrollments:
        student = enrollment.student
        
        # Get quiz attempts for this class
        quiz_attempts = QuizAttempt.objects.filter(
            student=student,
            quiz__assigned_classes=teacher_class
        ).order_by('-completed_at')
        
        # Calculate average score
        if quiz_attempts:
            avg_score = sum(attempt.score for attempt in quiz_attempts) / len(quiz_attempts)
        else:
            avg_score = 0
        
        student_progress.append({
            'student': student,
            'enrollment': enrollment,
            'quiz_attempts': quiz_attempts[:5],  # Last 5 attempts
            'total_attempts': quiz_attempts.count(),
            'average_score': avg_score,
        })
    
    context = {
        'teacher_class': teacher_class,
        'student_progress': student_progress,
        'teacher_profile': teacher_profile,
    }
    
    return render(request, 'learning/student_progress.html', context)


@login_required
@teacher_required
@require_http_methods(["POST"])
def remove_student(request, class_id, student_id):
    """Remove a student from a class"""
    teacher_profile = request.user.teacher_profile
    teacher_class = get_object_or_404(
        TeacherClass,
        id=class_id,
        teacher=teacher_profile
    )
    
    try:
        enrollment = ClassEnrollment.objects.get(
            teacher_class=teacher_class,
            student_id=student_id,
            is_active=True
        )
        enrollment.is_active = False
        enrollment.save()
        
        messages.success(request, 'Student removed from class successfully.')
    except ClassEnrollment.DoesNotExist:
        messages.error(request, 'Student not found in this class.')
    
    return redirect('class_detail', class_id=class_id)


@login_required
@teacher_required
@require_http_methods(["POST"])
def toggle_quiz_status(request, quiz_id):
    """Toggle quiz active status"""
    teacher_profile = request.user.teacher_profile
    teacher_quiz = get_object_or_404(
        TeacherQuiz,
        id=quiz_id,
        teacher=teacher_profile
    )
    
    teacher_quiz.is_active = not teacher_quiz.is_active
    teacher_quiz.save()
    
    status = "activated" if teacher_quiz.is_active else "deactivated"
    messages.success(request, f'Quiz "{teacher_quiz.title}" has been {status}.')
    
    return redirect('teacher_quiz_list')


@login_required
@teacher_required
def quiz_analytics(request, quiz_id):
    """View analytics for a specific quiz"""
    teacher_profile = request.user.teacher_profile
    teacher_quiz = get_object_or_404(
        TeacherQuiz,
        id=quiz_id,
        teacher=teacher_profile
    )
    
    # Get all attempts for this quiz
    attempts = QuizAttempt.objects.filter(quiz=teacher_quiz).select_related('student__user')
    
    # Calculate statistics
    total_attempts = attempts.count()
    unique_students = attempts.values('student').distinct().count()
    
    if total_attempts > 0:
        average_score = sum(attempt.score for attempt in attempts) / total_attempts
        average_time = sum(attempt.time_taken_minutes for attempt in attempts) / total_attempts
    else:
        average_score = 0
        average_time = 0
    
    # Get score distribution
    score_ranges = {
        '90-100': attempts.filter(score__gte=90).count(),
        '80-89': attempts.filter(score__gte=80, score__lt=90).count(),
        '70-79': attempts.filter(score__gte=70, score__lt=80).count(),
        '60-69': attempts.filter(score__gte=60, score__lt=70).count(),
        'Below 60': attempts.filter(score__lt=60).count(),
    }
    
    # Get recent attempts
    recent_attempts = attempts.order_by('-completed_at')[:10]
    
    context = {
        'teacher_quiz': teacher_quiz,
        'total_attempts': total_attempts,
        'unique_students': unique_students,
        'average_score': round(average_score, 1),
        'average_time': round(average_time, 1),
        'score_ranges': score_ranges,
        'recent_attempts': recent_attempts,
        'teacher_profile': teacher_profile,
    }
    
    return render(request, 'learning/quiz_analytics.html', context)


# AJAX endpoints for dynamic functionality

@login_required
@teacher_required
@csrf_exempt
def update_quiz_questions(request):
    """AJAX endpoint to update quiz questions"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            quiz_id = data.get('quiz_id')
            questions = data.get('questions', [])
            
            teacher_profile = request.user.teacher_profile
            teacher_quiz = get_object_or_404(
                TeacherQuiz,
                id=quiz_id,
                teacher=teacher_profile
            )
            
            teacher_quiz.customized_questions = questions
            teacher_quiz.save()
            
            return JsonResponse({'success': True, 'message': 'Questions updated successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@teacher_required
def get_class_students(request, class_id):
    """AJAX endpoint to get students in a class"""
    teacher_profile = request.user.teacher_profile
    teacher_class = get_object_or_404(
        TeacherClass,
        id=class_id,
        teacher=teacher_profile
    )
    
    students = []
    for enrollment in teacher_class.enrollments.filter(is_active=True):
        students.append({
            'id': enrollment.student.id,
            'username': enrollment.student.user.username,
            'email': enrollment.student.user.email,
            'enrolled_at': enrollment.enrolled_at.isoformat(),
        })
    
    return JsonResponse({'students': students})


@login_required
@teacher_required
def content_processing_status(request, content_id):
    """AJAX endpoint to check content processing status"""
    teacher_profile = request.user.teacher_profile
    teacher_content = get_object_or_404(
        TeacherContent,
        id=content_id,
        teacher=teacher_profile
    )
    
    uploaded_content = teacher_content.uploaded_content
    
    return JsonResponse({
        'status': uploaded_content.processing_status,
        'processed_at': uploaded_content.processed_at.isoformat() if uploaded_content.processed_at else None,
        'has_summaries': uploaded_content.summaries.exists(),
        'has_quizzes': uploaded_content.quizzes.exists(),
        'has_flashcards': uploaded_content.flashcards.exists(),
    })