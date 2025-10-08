"""
Celery tasks for asynchronous content processing.
"""

import logging
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from .models import UploadedContent
from .services import content_processor
from .ai_services import ai_content_generator

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_uploaded_content(self, content_id):
    """
    Asynchronous task to process uploaded content.
    
    Args:
        content_id (int): ID of the UploadedContent instance to process
        
    Returns:
        dict: Processing results
    """
    try:
        # Get the uploaded content
        try:
            uploaded_content = UploadedContent.objects.get(id=content_id)
        except UploadedContent.DoesNotExist:
            logger.error(f"UploadedContent with ID {content_id} not found")
            return {'success': False, 'error': 'Content not found'}
        
        # Update status to processing
        uploaded_content.processing_status = 'processing'
        uploaded_content.save()
        
        logger.info(f"Starting processing for content: {uploaded_content.original_filename}")
        
        # Process the content (extract text)
        result = content_processor.process_content(uploaded_content)
        
        if result['success']:
            # Generate AI content (summaries, quizzes, flashcards)
            logger.info(f"Starting AI content generation for: {uploaded_content.original_filename}")
            ai_result = ai_content_generator.generate_all_content(uploaded_content)
            
            # Mark processing as completed
            uploaded_content.processed_at = timezone.now()
            uploaded_content.save()
            
            # Add AI generation results to the main result
            result['ai_generation'] = ai_result
            
            # Send notification to user (optional)
            if hasattr(uploaded_content.user, 'email') and uploaded_content.user.email:
                send_processing_complete_notification.delay(
                    uploaded_content.user.email,
                    uploaded_content.original_filename
                )
            
            logger.info(f"Successfully processed content: {uploaded_content.original_filename}")
            return {
                'success': True,
                'content_id': content_id,
                'filename': uploaded_content.original_filename,
                'word_count': result.get('word_count', 0),
                'processing_time': str(timezone.now() - uploaded_content.created_at)
            }
        else:
            # Processing failed
            logger.error(f"Processing failed for content: {uploaded_content.original_filename}")
            return {
                'success': False,
                'content_id': content_id,
                'filename': uploaded_content.original_filename,
                'error': result.get('error', 'Unknown error')
            }
            
    except Exception as exc:
        # Log the error
        logger.error(f"Task failed for content ID {content_id}: {str(exc)}")
        
        # Update content status to failed
        try:
            uploaded_content = UploadedContent.objects.get(id=content_id)
            uploaded_content.processing_status = 'failed'
            uploaded_content.save()
        except UploadedContent.DoesNotExist:
            pass
        
        # Retry the task if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task for content ID {content_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'content_id': content_id,
            'error': str(exc),
            'retries_exhausted': True
        }


@shared_task
def send_processing_complete_notification(user_email, filename):
    """
    Send email notification when content processing is complete.
    
    Args:
        user_email (str): User's email address
        filename (str): Name of the processed file
    """
    try:
        subject = f"Content Processing Complete - {filename}"
        message = f"""
        Hello,
        
        Your uploaded content "{filename}" has been successfully processed and is now ready for learning!
        
        You can now:
        - View generated summaries
        - Take AI-generated quizzes
        - Study with flashcards
        
        Log in to your dashboard to start learning: {settings.LOGIN_REDIRECT_URL}
        
        Best regards,
        The Metlab.edu Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        
        logger.info(f"Processing notification sent to {user_email} for file {filename}")
        return {'success': True, 'email': user_email}
        
    except Exception as e:
        logger.error(f"Failed to send notification to {user_email}: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def cleanup_failed_uploads():
    """
    Periodic task to clean up failed uploads and orphaned files.
    This task should be run periodically (e.g., daily) to maintain system health.
    """
    try:
        from datetime import timedelta
        
        # Find uploads that have been in 'processing' state for more than 1 hour
        cutoff_time = timezone.now() - timedelta(hours=1)
        stale_uploads = UploadedContent.objects.filter(
            processing_status='processing',
            created_at__lt=cutoff_time
        )
        
        stale_count = 0
        for upload in stale_uploads:
            upload.processing_status = 'failed'
            upload.save()
            stale_count += 1
            logger.warning(f"Marked stale upload as failed: {upload.original_filename}")
        
        # Find uploads that have been in 'failed' state for more than 7 days
        old_failed_cutoff = timezone.now() - timedelta(days=7)
        old_failed_uploads = UploadedContent.objects.filter(
            processing_status='failed',
            created_at__lt=old_failed_cutoff
        )
        
        deleted_count = 0
        for upload in old_failed_uploads:
            # Delete the file if it exists
            if upload.file:
                try:
                    upload.file.delete(save=False)
                except Exception as e:
                    logger.warning(f"Could not delete file for {upload.original_filename}: {str(e)}")
            
            # Delete the database record
            upload.delete()
            deleted_count += 1
            logger.info(f"Cleaned up old failed upload: {upload.original_filename}")
        
        logger.info(f"Cleanup complete: {stale_count} stale uploads marked as failed, {deleted_count} old failed uploads deleted")
        
        return {
            'success': True,
            'stale_uploads_fixed': stale_count,
            'old_uploads_deleted': deleted_count
        }
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def generate_ai_content(self, content_id):
    """
    Asynchronous task to generate AI content (summaries, quizzes, flashcards).
    
    Args:
        content_id (int): ID of the UploadedContent instance
        
    Returns:
        dict: AI generation results
    """
    try:
        # Get the uploaded content
        try:
            uploaded_content = UploadedContent.objects.get(id=content_id)
        except UploadedContent.DoesNotExist:
            logger.error(f"UploadedContent with ID {content_id} not found")
            return {'success': False, 'error': 'Content not found'}
        
        if not uploaded_content.extracted_text:
            logger.error(f"No extracted text available for content ID {content_id}")
            return {'success': False, 'error': 'No extracted text available'}
        
        logger.info(f"Starting AI content generation for: {uploaded_content.original_filename}")
        
        # Generate AI content
        result = ai_content_generator.generate_all_content(uploaded_content)
        
        if result['success']:
            logger.info(f"AI content generation completed for: {uploaded_content.original_filename}")
            return {
                'success': True,
                'content_id': content_id,
                'filename': uploaded_content.original_filename,
                'concepts_count': len(result.get('concepts', [])),
                'summaries_count': len(result.get('summaries', {})),
                'quiz_questions': len(result.get('quizzes', [])),
                'flashcards_count': len(result.get('flashcards', [])),
                'errors': result.get('errors', [])
            }
        else:
            logger.error(f"AI content generation failed for: {uploaded_content.original_filename}")
            return {
                'success': False,
                'content_id': content_id,
                'filename': uploaded_content.original_filename,
                'errors': result.get('errors', ['Unknown error'])
            }
            
    except Exception as exc:
        logger.error(f"AI content generation task failed for content ID {content_id}: {str(exc)}")
        
        # Retry the task if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying AI generation for content ID {content_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=120 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'content_id': content_id,
            'error': str(exc),
            'retries_exhausted': True
        }


@shared_task
def batch_process_content(content_ids):
    """
    Process multiple content files in batch.
    
    Args:
        content_ids (list): List of UploadedContent IDs to process
        
    Returns:
        dict: Batch processing results
    """
    results = {
        'success': True,
        'processed': [],
        'failed': [],
        'total': len(content_ids)
    }
    
    for content_id in content_ids:
        try:
            result = process_uploaded_content.delay(content_id)
            results['processed'].append({
                'content_id': content_id,
                'task_id': result.id
            })
        except Exception as e:
            logger.error(f"Failed to queue processing for content ID {content_id}: {str(e)}")
            results['failed'].append({
                'content_id': content_id,
                'error': str(e)
            })
            results['success'] = False
    
    logger.info(f"Batch processing queued: {len(results['processed'])} successful, {len(results['failed'])} failed")
    return results