import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from accounts.decorators import role_required
from .models import UploadedContent, GeneratedSummary, GeneratedQuiz, Flashcard
from .forms import ContentUploadForm
from .tasks import process_uploaded_content

logger = logging.getLogger(__name__)


@login_required
@role_required(['student', 'teacher'])
def upload_content(request):
    """View for uploading content files"""
    if request.method == 'POST':
        form = ContentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Create the uploaded content record
                uploaded_content = form.save(commit=False)
                uploaded_content.user = request.user
                uploaded_content.save()
                
                # Queue the content for processing
                process_uploaded_content.delay(uploaded_content.id)
                
                messages.success(
                    request, 
                    f'File "{uploaded_content.original_filename}" uploaded successfully! '
                    'Processing will begin shortly.'
                )
                
                # Return JSON response for AJAX requests
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'File uploaded successfully!',
                        'content_id': uploaded_content.id,
                        'filename': uploaded_content.original_filename,
                        'redirect_url': '/content/library/'
                    })
                
                return redirect('content:library')
                
            except Exception as e:
                logger.error(f"Upload failed for user {request.user.username}: {str(e)}")
                messages.error(request, f'Upload failed: {str(e)}')
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
        else:
            # Form validation errors
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
    else:
        form = ContentUploadForm()
    
    return render(request, 'content/upload.html', {'form': form})


@login_required
@role_required(['student', 'teacher'])
def content_library(request):
    """View for displaying user's uploaded content library"""
    # Get user's content
    content_list = UploadedContent.objects.filter(user=request.user).order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        content_list = content_list.filter(
            Q(original_filename__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(extracted_text__icontains=search_query)
        )
    
    # Filter by processing status
    status_filter = request.GET.get('status', '')
    if status_filter:
        content_list = content_list.filter(processing_status=status_filter)
    
    # Filter by content type
    type_filter = request.GET.get('type', '')
    if type_filter:
        content_list = content_list.filter(content_type=type_filter)
    
    # Pagination
    paginator = Paginator(content_list, 12)  # Show 12 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get processing status counts for filters
    status_counts = {
        'all': UploadedContent.objects.filter(user=request.user).count(),
        'completed': UploadedContent.objects.filter(user=request.user, processing_status='completed').count(),
        'processing': UploadedContent.objects.filter(user=request.user, processing_status='processing').count(),
        'failed': UploadedContent.objects.filter(user=request.user, processing_status='failed').count(),
    }
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'status_counts': status_counts,
    }
    
    return render(request, 'content/library.html', context)


@login_required
@role_required(['student', 'teacher'])
def content_detail(request, content_id):
    """View for displaying detailed content information and generated materials"""
    content = get_object_or_404(UploadedContent, id=content_id, user=request.user)
    
    # Get generated materials
    summaries = GeneratedSummary.objects.filter(content=content).order_by('summary_type')
    quizzes = GeneratedQuiz.objects.filter(content=content).order_by('-generated_at')
    flashcards = Flashcard.objects.filter(content=content).order_by('order_index')
    
    context = {
        'content': content,
        'summaries': summaries,
        'quizzes': quizzes,
        'flashcards': flashcards,
    }
    
    return render(request, 'content/detail.html', context)


@login_required
@role_required(['student', 'teacher'])
def download_content(request, content_id):
    """View for downloading original content files"""
    content = get_object_or_404(UploadedContent, id=content_id, user=request.user)
    
    try:
        if content.file:
            response = HttpResponse(content.file.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{content.original_filename}"'
            return response
        else:
            raise Http404("File not found")
    except Exception as e:
        logger.error(f"Download failed for content {content_id}: {str(e)}")
        messages.error(request, "File download failed.")
        return redirect('content:detail', content_id=content_id)


@login_required
@role_required(['student', 'teacher'])
def delete_content(request, content_id):
    """View for deleting uploaded content"""
    content = get_object_or_404(UploadedContent, id=content_id, user=request.user)
    
    if request.method == 'POST':
        try:
            filename = content.original_filename
            
            # Delete the file
            if content.file:
                content.file.delete(save=False)
            
            # Delete the database record (this will cascade to related objects)
            content.delete()
            
            messages.success(request, f'Content "{filename}" deleted successfully.')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Content deleted successfully.'})
            
            return redirect('content:library')
            
        except Exception as e:
            logger.error(f"Delete failed for content {content_id}: {str(e)}")
            messages.error(request, f'Delete failed: {str(e)}')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
    
    return render(request, 'content/delete_confirm.html', {'content': content})


@login_required
@role_required(['student', 'teacher'])
def processing_status(request, content_id):
    """AJAX endpoint for checking content processing status"""
    content = get_object_or_404(UploadedContent, id=content_id, user=request.user)
    
    return JsonResponse({
        'status': content.processing_status,
        'processed_at': content.processed_at.isoformat() if content.processed_at else None,
        'has_summaries': content.summaries.exists(),
        'has_quizzes': content.quizzes.exists(),
        'has_flashcards': content.flashcards.exists(),
        'word_count': len(content.extracted_text.split()) if content.extracted_text else 0,
    })


@login_required
@role_required(['student', 'teacher'])
def quiz_view(request, quiz_id):
    """View for taking a generated quiz"""
    quiz = get_object_or_404(GeneratedQuiz, id=quiz_id, content__user=request.user)
    
    context = {
        'quiz': quiz,
        'questions': quiz.questions,
    }
    
    return render(request, 'content/quiz.html', context)


@login_required
@role_required(['student', 'teacher'])
def flashcards_view(request, content_id):
    """View for studying flashcards"""
    content = get_object_or_404(UploadedContent, id=content_id, user=request.user)
    flashcards = Flashcard.objects.filter(content=content).order_by('order_index')
    
    if not flashcards.exists():
        messages.info(request, "No flashcards available for this content yet.")
        return redirect('content:detail', content_id=content_id)
    
    context = {
        'content': content,
        'flashcards': flashcards,
        'total_cards': flashcards.count(),
    }
    
    return render(request, 'content/flashcards.html', context)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def upload_progress(request):
    """AJAX endpoint for file upload progress (placeholder for future implementation)"""
    # This would typically integrate with a file upload progress tracking system
    # For now, return a simple response
    return JsonResponse({
        'progress': 100,
        'status': 'complete'
    })
