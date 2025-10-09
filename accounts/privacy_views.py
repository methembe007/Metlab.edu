"""
Privacy management views for GDPR/COPPA compliance
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from metlab_edu.rate_limiting import rate_limit
import json
import logging

from .models import (
    PrivacyConsent, DataDeletionRequest, DataExportRequest, 
    AuditLog, COPPACompliance
)

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def privacy_settings(request):
    """Privacy settings page for users"""
    user = request.user
    
    # Get current consents
    consents = {}
    for consent_type, _ in PrivacyConsent.CONSENT_TYPES:
        try:
            consent = PrivacyConsent.objects.get(user=user, consent_type=consent_type)
            consents[consent_type] = consent.granted
        except PrivacyConsent.DoesNotExist:
            consents[consent_type] = False
    
    # Get COPPA compliance info if applicable
    coppa_compliance = None
    try:
        coppa_compliance = COPPACompliance.objects.get(user=user)
    except COPPACompliance.DoesNotExist:
        pass
    
    # Get recent data requests
    deletion_requests = DataDeletionRequest.objects.filter(user=user)[:5]
    export_requests = DataExportRequest.objects.filter(user=user)[:5]
    
    context = {
        'consents': consents,
        'coppa_compliance': coppa_compliance,
        'deletion_requests': deletion_requests,
        'export_requests': export_requests,
        'privacy_policy_version': getattr(settings, 'PRIVACY_POLICY_VERSION', '1.0'),
    }
    
    return render(request, 'accounts/privacy_settings.html', context)


@login_required
@require_http_methods(["POST"])
@rate_limit(rate='10/m')
def update_consent(request):
    """Update user privacy consent"""
    try:
        data = json.loads(request.body)
        consent_type = data.get('consent_type')
        granted = data.get('granted', False)
        
        if consent_type not in dict(PrivacyConsent.CONSENT_TYPES):
            return JsonResponse({'error': 'Invalid consent type'}, status=400)
        
        # Get or create consent record
        consent, created = PrivacyConsent.objects.get_or_create(
            user=request.user,
            consent_type=consent_type,
            defaults={
                'privacy_policy_version': getattr(settings, 'PRIVACY_POLICY_VERSION', '1.0')
            }
        )
        
        # Update consent
        if granted:
            consent.grant_consent(
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        else:
            consent.withdraw_consent()
        
        # Log the action
        AuditLog.objects.create(
            user=request.user,
            action='update',
            resource_type='privacy_consent',
            resource_id=consent_type,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details={'granted': granted}
        )
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        logger.error(f"Error updating consent: {str(e)}")
        return JsonResponse({'error': 'Failed to update consent'}, status=500)


@login_required
@require_http_methods(["POST"])
@rate_limit(rate='3/h')
def request_data_deletion(request):
    """Request data deletion (Right to be Forgotten)"""
    try:
        # Check if user already has a pending request
        existing_request = DataDeletionRequest.objects.filter(
            user=request.user,
            status__in=['pending', 'processing']
        ).first()
        
        if existing_request:
            return JsonResponse({
                'error': 'You already have a pending deletion request'
            }, status=400)
        
        # Create deletion request
        deletion_request = DataDeletionRequest.objects.create(
            user=request.user,
            reason=request.POST.get('reason', '')
        )
        
        # Log the action
        AuditLog.objects.create(
            user=request.user,
            action='create',
            resource_type='data_deletion_request',
            resource_id=str(deletion_request.id),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details={'reason': deletion_request.reason}
        )
        
        # Send notification email to admins
        try:
            send_mail(
                subject='Data Deletion Request',
                message=f'User {request.user.username} has requested data deletion.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],  # Admin email
                fail_silently=True
            )
        except Exception as e:
            logger.error(f"Failed to send deletion request email: {str(e)}")
        
        messages.success(request, 'Your data deletion request has been submitted.')
        return JsonResponse({'success': True})
        
    except Exception as e:
        logger.error(f"Error creating deletion request: {str(e)}")
        return JsonResponse({'error': 'Failed to create deletion request'}, status=500)


@login_required
@require_http_methods(["POST"])
@rate_limit(rate='5/d')
def request_data_export(request):
    """Request data export (Right to Data Portability)"""
    try:
        # Check if user already has a pending request
        existing_request = DataExportRequest.objects.filter(
            user=request.user,
            status__in=['pending', 'processing', 'ready']
        ).first()
        
        if existing_request:
            return JsonResponse({
                'error': 'You already have a pending export request'
            }, status=400)
        
        # Create export request
        export_request = DataExportRequest.objects.create(user=request.user)
        
        # Log the action
        AuditLog.objects.create(
            user=request.user,
            action='create',
            resource_type='data_export_request',
            resource_id=str(export_request.id),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        # Send notification email to admins
        try:
            send_mail(
                subject='Data Export Request',
                message=f'User {request.user.username} has requested data export.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],  # Admin email
                fail_silently=True
            )
        except Exception as e:
            logger.error(f"Failed to send export request email: {str(e)}")
        
        messages.success(request, 'Your data export request has been submitted.')
        return JsonResponse({'success': True})
        
    except Exception as e:
        logger.error(f"Error creating export request: {str(e)}")
        return JsonResponse({'error': 'Failed to create export request'}, status=500)


@login_required
def download_data_export(request, request_id):
    """Download data export file"""
    export_request = get_object_or_404(
        DataExportRequest,
        id=request_id,
        user=request.user,
        status='ready'
    )
    
    # Check if export has expired
    if export_request.expires_at and export_request.expires_at < timezone.now():
        export_request.status = 'expired'
        export_request.save()
        messages.error(request, 'This export has expired. Please request a new one.')
        return redirect('accounts:privacy_settings')
    
    # Record download
    export_request.record_download()
    
    # Log the action
    AuditLog.objects.create(
        user=request.user,
        action='export',
        resource_type='user_data',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        details={'export_request_id': request_id}
    )
    
    # In a real implementation, you would serve the actual file
    # For now, we'll redirect to the download URL
    if export_request.download_url:
        return redirect(export_request.download_url)
    else:
        messages.error(request, 'Export file not available.')
        return redirect('accounts:privacy_settings')


@require_http_methods(["POST"])
@csrf_exempt
@rate_limit(rate='10/m')
def coppa_parent_verification(request):
    """Handle COPPA parent verification"""
    try:
        token = request.POST.get('token')
        if not token:
            return JsonResponse({'error': 'Verification token required'}, status=400)
        
        # Find COPPA compliance record
        coppa_compliance = get_object_or_404(
            COPPACompliance,
            verification_token=token
        )
        
        # Verify parent consent
        coppa_compliance.verify_parent_consent()
        
        # Log the action
        AuditLog.objects.create(
            user=coppa_compliance.user,
            action='update',
            resource_type='coppa_compliance',
            resource_id=str(coppa_compliance.id),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details={'parent_consent_verified': True}
        )
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        logger.error(f"Error verifying COPPA consent: {str(e)}")
        return JsonResponse({'error': 'Verification failed'}, status=500)


@login_required
def audit_log(request):
    """View user's audit log"""
    logs = AuditLog.objects.filter(user=request.user)[:100]  # Last 100 entries
    
    return render(request, 'accounts/audit_log.html', {
        'logs': logs
    })