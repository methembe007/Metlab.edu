"""
Views for students to access teacher-assigned content
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, Http404, FileResponse
from django.core.paginator import Paginator
from django.db.models import Q
import logging
import mimetypes

from accounts.decorators import role_required
from accounts.models import StudentProfile
from .teacher_models import TeacherClass, ClassEnrollment, TeacherContent
from content.models import UploadedContent

logger = logging.getLogger(__name__)


@login_required
@role_required(['student'])
def my_classes(request):
    """View all classes the student is enrolled in"""
    student_profile = request.user.student_profile
    
    # Get active enrollments
    enrollments = ClassEnrollment.objects.filter(
        student=student_profile,
        is_active=True
    ).select_related('teacher_class__teacher__user').order_by('-enrolled_at')
    
    context = {
        'enrollments': enrollments,
        'student_profile': student_profile,
    }
    
    return render(request, 'learning/student_classes.html', context)


@login_required
@role_required(['student'])
def class_content(request, class_id):
    """View all content assigned to a specific class"""
    student_profile = request.user.student_profile
    
    # Verify student is enrolled in this class
    enrollment = get_object_or_404(
        ClassEnrollment,
        teacher_class_id=class_id,
        student=student_profile,
        is_active=True
    )
    
    teacher_class = enrollment.teacher_class
    
    # Get all content assigned to this class
    assigned_content = teacher_class.assigned_content.select_related(
        'uploaded_content', 'teacher__user'
    ).order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        assigned_content = assigned_content.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(subject__icontains=search_query)
        )
    
    # Filter by subject
    subject_filter = request.GET.get('subject', '')
    if subject_filter:
        assigned_content = assigned_content.filter(subject=subject_filter)
    
    # Get unique subjects for filter dropdown
    subjects = teacher_class.assigned_content.values_list('subject', flat=True).distinct()
    
    # Pagination
    paginator = Paginator(assigned_content, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'teacher_class': teacher_class,
        'enrollment': enrollment,
        'page_obj': page_obj,
        'search_query': search_query,
        'subject_filter': subject_filter,
        'subjects': subjects,
        'student_profile': student_profile,
    }
    
    return render(request, 'learning/student_class_content.html', context)


@login_required
@role_required(['student'])
def view_content(request, content_id):
    """View details of a specific piece of content"""
    student_profile = request.user.student_profile
    
    # Get the teacher content
    teacher_content = get_object_or_404(TeacherContent, id=content_id)
    
    # Verify student has access (enrolled in at least one class with this content)
    student_classes = ClassEnrollment.objects.filter(
        student=student_profile,
        is_active=True
    ).values_list('teacher_class_id', flat=True)
    
    if not teacher_content.assigned_classes.filter(id__in=student_classes).exists():
        messages.error(request, "You don't have access to this content.")
        return redirect('learning:my_classes')
    
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
        'student_profile': student_profile,
    }
    
    return render(request, 'learning/student_content_detail.html', context)


@login_required
@role_required(['student'])
def view_pdf(request, content_id):
    """View PDF file in browser"""
    student_profile = request.user.student_profile
    
    # Get the teacher content
    teacher_content = get_object_or_404(TeacherContent, id=content_id)
    
    # Verify student has access
    student_classes = ClassEnrollment.objects.filter(
        student=student_profile,
        is_active=True
    ).values_list('teacher_class_id', flat=True)
    
    if not teacher_content.assigned_classes.filter(id__in=student_classes).exists():
        raise Http404("You don't have access to this content.")
    
    uploaded_content = teacher_content.uploaded_content
    
    # Check if file exists and is a PDF
    if not uploaded_content.file:
        raise Http404("File not found")
    
    if uploaded_content.content_type != 'pdf':
        messages.error(request, "This file is not a PDF.")
        return redirect('learning:view_content', content_id=content_id)
    
    try:
        # Open the file
        file_path = uploaded_content.file.path
        
        # Return the PDF file for viewing in browser
        response = FileResponse(
            open(file_path, 'rb'),
            content_type='application/pdf'
        )
        
        # Set headers to display in browser instead of downloading
        response['Content-Disposition'] = f'inline; filename="{uploaded_content.original_filename}"'
        
        # Allow iframe embedding from same origin
        response['X-Frame-Options'] = 'SAMEORIGIN'
        
        # Add cache control for better performance
        response['Cache-Control'] = 'public, max-age=3600'
        
        return response
        
    except Exception as e:
        logger.error(f"Error viewing PDF {content_id}: {str(e)}")
        messages.error(request, "Error loading PDF file.")
        return redirect('learning:view_content', content_id=content_id)
        return redirect('learning:view_content', content_id=content_id)


@login_required
@role_required(['student'])
def download_content(request, content_id):
    """Download content file"""
    student_profile = request.user.student_profile
    
    # Get the teacher content
    teacher_content = get_object_or_404(TeacherContent, id=content_id)
    
    # Verify student has access
    student_classes = ClassEnrollment.objects.filter(
        student=student_profile,
        is_active=True
    ).values_list('teacher_class_id', flat=True)
    
    if not teacher_content.assigned_classes.filter(id__in=student_classes).exists():
        raise Http404("You don't have access to this content.")
    
    uploaded_content = teacher_content.uploaded_content
    
    if not uploaded_content.file:
        raise Http404("File not found")
    
    try:
        # Get the file
        file_path = uploaded_content.file.path
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'application/octet-stream'
        
        # Create response
        response = FileResponse(
            open(file_path, 'rb'),
            content_type=content_type
        )
        
        # Set headers for download
        response['Content-Disposition'] = f'attachment; filename="{uploaded_content.original_filename}"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error downloading content {content_id}: {str(e)}")
        messages.error(request, "Error downloading file.")
        return redirect('learning:view_content', content_id=content_id)


@login_required
@role_required(['student'])
def all_assigned_content(request):
    """View all content assigned across all enrolled classes"""
    student_profile = request.user.student_profile
    
    # Get all classes student is enrolled in
    student_classes = ClassEnrollment.objects.filter(
        student=student_profile,
        is_active=True
    ).values_list('teacher_class_id', flat=True)
    
    # Get all content assigned to these classes
    assigned_content = TeacherContent.objects.filter(
        assigned_classes__id__in=student_classes
    ).select_related(
        'uploaded_content', 'teacher__user'
    ).distinct().order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        assigned_content = assigned_content.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(subject__icontains=search_query)
        )
    
    # Filter by subject
    subject_filter = request.GET.get('subject', '')
    if subject_filter:
        assigned_content = assigned_content.filter(subject=subject_filter)
    
    # Filter by file type
    file_type_filter = request.GET.get('file_type', '')
    if file_type_filter:
        assigned_content = assigned_content.filter(uploaded_content__content_type=file_type_filter)
    
    # Get unique subjects for filter dropdown
    subjects = TeacherContent.objects.filter(
        assigned_classes__id__in=student_classes
    ).values_list('subject', flat=True).distinct()
    
    # Pagination
    paginator = Paginator(assigned_content, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'subject_filter': subject_filter,
        'file_type_filter': file_type_filter,
        'subjects': subjects,
        'student_profile': student_profile,
        'total_content': assigned_content.count(),
    }
    
    return render(request, 'learning/student_all_content.html', context)
