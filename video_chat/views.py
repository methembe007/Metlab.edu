"""
Views for video chat session management.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.exceptions import PermissionDenied, ValidationError
from datetime import timedelta
from .models import VideoSession, VideoSessionParticipant
from .services import VideoSessionService
from .forms import VideoSessionScheduleForm, VideoSessionQuickStartForm, VideoSessionEditForm


@login_required
def schedule_session(request):
    """
    View for scheduling a new video session.
    Requirements: 5.1, 5.2
    """
    # Check if coming from class management
    class_id = request.session.get('video_session_class_id')
    class_name = request.session.get('video_session_class_name')
    student_ids = request.session.get('video_session_student_ids', [])
    
    if request.method == 'POST':
        form = VideoSessionScheduleForm(request.POST, user=request.user)
        
        if form.is_valid():
            try:
                # Create the session
                session = VideoSessionService.create_session(
                    host=request.user,
                    session_type=form.cleaned_data['session_type'],
                    title=form.cleaned_data['title'],
                    description=form.cleaned_data['description'],
                    scheduled_time=form.cleaned_data['scheduled_time'],
                    duration_minutes=form.cleaned_data['duration_minutes'],
                    max_participants=form.cleaned_data['max_participants'],
                    allow_screen_share=form.cleaned_data['allow_screen_share'],
                    require_approval=form.cleaned_data['require_approval'],
                    teacher_class=form.cleaned_data.get('teacher_class'),
                    tutor_booking=form.cleaned_data.get('tutor_booking')
                )
                
                # Add selected participants
                participants = form.cleaned_data.get('participants', [])
                for participant_user in participants:
                    VideoSessionParticipant.objects.create(
                        session=session,
                        user=participant_user,
                        role='participant',
                        status='invited'
                    )
                
                # Record attendance for class sessions
                if session.teacher_class:
                    from learning.teacher_models import ClassEnrollment
                    enrollments = ClassEnrollment.objects.filter(
                        teacher_class=session.teacher_class,
                        is_active=True
                    )
                    # Attendance will be recorded when students join the session
                
                # Send notifications to participants
                from .notifications import VideoSessionNotificationService
                VideoSessionNotificationService.send_session_scheduled_notification(
                    session, participants
                )
                
                # Clear session data
                if 'video_session_class_id' in request.session:
                    del request.session['video_session_class_id']
                if 'video_session_class_name' in request.session:
                    del request.session['video_session_class_name']
                if 'video_session_student_ids' in request.session:
                    del request.session['video_session_student_ids']
                
                messages.success(
                    request,
                    f'Video session "{session.title}" scheduled successfully for {session.scheduled_time.strftime("%B %d, %Y at %I:%M %p")}'
                )
                
                return redirect('video_chat:session_detail', session_id=session.session_id)
                
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Error scheduling session: {str(e)}')
    else:
        # Pre-fill form with class data if available
        initial_data = {}
        if class_id and class_name:
            initial_data['title'] = f"{class_name} - Video Session"
            initial_data['session_type'] = 'class'
            
            # Get the teacher class
            try:
                from learning.teacher_models import TeacherClass
                teacher_class = TeacherClass.objects.get(id=class_id)
                initial_data['teacher_class'] = teacher_class
            except:
                pass
        
        form = VideoSessionScheduleForm(user=request.user, initial=initial_data)
        
        # Pre-select students if coming from class
        if student_ids:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            form.fields['participants'].initial = User.objects.filter(id__in=student_ids)
    
    return render(request, 'video_chat/schedule_session.html', {
        'form': form,
        'page_title': 'Schedule Video Session',
        'from_class': bool(class_id)
    })


@login_required
def quick_start_session(request):
    """
    View for quickly starting an immediate video session.
    Requirements: 1.1, 1.2
    """
    if request.method == 'POST':
        form = VideoSessionQuickStartForm(request.POST, user=request.user)
        
        if form.is_valid():
            try:
                # Create and immediately start the session
                session = VideoSessionService.create_session(
                    host=request.user,
                    session_type=form.cleaned_data['session_type'],
                    title=form.cleaned_data['title'],
                    scheduled_time=timezone.now(),
                    duration_minutes=60,
                    allow_screen_share=form.cleaned_data['allow_screen_share']
                )
                
                # Add selected participants
                participants = form.cleaned_data.get('participants', [])
                for participant_user in participants:
                    VideoSessionParticipant.objects.create(
                        session=session,
                        user=participant_user,
                        role='participant',
                        status='invited'
                    )
                
                # Start the session immediately
                VideoSessionService.start_session(session.session_id, request.user)
                
                messages.success(request, f'Video session "{session.title}" started successfully')
                
                return redirect('video_chat:join_session', session_id=session.session_id)
                
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Error starting session: {str(e)}')
    else:
        form = VideoSessionQuickStartForm(user=request.user)
    
    return render(request, 'video_chat/quick_start.html', {
        'form': form,
        'page_title': 'Start Video Session'
    })


@login_required
def session_list(request):
    """
    View for listing user's video sessions.
    Requirements: 5.1, 8.2
    """
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')
    
    # Get user's sessions
    if status_filter == 'all':
        sessions = VideoSessionService.get_user_sessions(request.user)
    else:
        sessions = VideoSessionService.get_user_sessions(request.user, status=status_filter)
    
    # Separate upcoming and past sessions
    now = timezone.now()
    upcoming_sessions = sessions.filter(
        scheduled_time__gte=now,
        status='scheduled'
    ).order_by('scheduled_time')
    
    active_sessions = sessions.filter(status='active')
    
    past_sessions = sessions.filter(
        status__in=['completed', 'cancelled']
    ).order_by('-created_at')[:20]  # Limit to 20 most recent
    
    return render(request, 'video_chat/session_list.html', {
        'upcoming_sessions': upcoming_sessions,
        'active_sessions': active_sessions,
        'past_sessions': past_sessions,
        'status_filter': status_filter,
        'page_title': 'My Video Sessions'
    })


@login_required
def session_detail(request, session_id):
    """
    View for displaying session details.
    Requirements: 5.1, 5.2, 8.2
    """
    try:
        session = VideoSessionService.get_session(session_id)
    except VideoSession.DoesNotExist:
        messages.error(request, 'Session not found')
        return redirect('video_chat:session_list')
    
    # Check if user has access to this session
    is_host = session.host == request.user
    is_participant = VideoSessionParticipant.objects.filter(
        session=session,
        user=request.user
    ).exists()
    
    if not (is_host or is_participant):
        messages.error(request, 'You do not have access to this session')
        return redirect('video_chat:session_list')
    
    # Get participant information
    participants = session.participants.select_related('user').all()
    
    # Check if session can be joined
    now = timezone.now()
    can_join = False
    
    if session.status == 'active':
        can_join = True
    elif session.status == 'scheduled' and session.scheduled_time:
        # Allow joining 10 minutes before scheduled time
        early_join_time = session.scheduled_time - timedelta(minutes=10)
        can_join = now >= early_join_time
    
    # Get session statistics if completed
    statistics = None
    if session.status == 'completed':
        try:
            statistics = VideoSessionService.get_session_statistics(session_id)
        except Exception:
            pass
    
    return render(request, 'video_chat/session_detail.html', {
        'session': session,
        'participants': participants,
        'is_host': is_host,
        'is_participant': is_participant,
        'can_join': can_join,
        'statistics': statistics,
        'page_title': session.title
    })


@login_required
def edit_session(request, session_id):
    """
    View for editing a scheduled session.
    Requirements: 5.1, 5.2
    """
    try:
        session = VideoSessionService.get_session(session_id)
    except VideoSession.DoesNotExist:
        messages.error(request, 'Session not found')
        return redirect('video_chat:session_list')
    
    # Only host can edit
    if session.host != request.user:
        messages.error(request, 'Only the session host can edit the session')
        return redirect('video_chat:session_detail', session_id=session_id)
    
    # Can only edit scheduled sessions
    if session.status != 'scheduled':
        messages.error(request, 'Only scheduled sessions can be edited')
        return redirect('video_chat:session_detail', session_id=session_id)
    
    if request.method == 'POST':
        form = VideoSessionEditForm(request.POST, instance=session)
        
        if form.is_valid():
            try:
                form.save()
                
                # Send update notification to participants
                from .notifications import VideoSessionNotificationService
                VideoSessionNotificationService.send_session_updated_notification(session)
                
                messages.success(request, 'Session updated successfully')
                return redirect('video_chat:session_detail', session_id=session_id)
            except Exception as e:
                messages.error(request, f'Error updating session: {str(e)}')
    else:
        # Format scheduled_time for datetime-local input
        initial_data = {}
        if session.scheduled_time:
            initial_data['scheduled_time'] = session.scheduled_time.strftime('%Y-%m-%dT%H:%M')
        
        form = VideoSessionEditForm(instance=session, initial=initial_data)
    
    return render(request, 'video_chat/edit_session.html', {
        'form': form,
        'session': session,
        'page_title': f'Edit {session.title}'
    })


@login_required
def cancel_session(request, session_id):
    """
    View for cancelling a scheduled session.
    Requirements: 5.2
    """
    try:
        session = VideoSessionService.get_session(session_id)
    except VideoSession.DoesNotExist:
        messages.error(request, 'Session not found')
        return redirect('video_chat:session_list')
    
    # Only host can cancel
    if session.host != request.user:
        messages.error(request, 'Only the session host can cancel the session')
        return redirect('video_chat:session_detail', session_id=session_id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        
        try:
            VideoSessionService.cancel_session(session_id, request.user, reason)
            
            # Send cancellation notification to participants
            from .notifications import VideoSessionNotificationService
            VideoSessionNotificationService.send_session_cancelled_notification(session, reason)
            
            messages.success(request, f'Session "{session.title}" has been cancelled')
            return redirect('video_chat:session_list')
        except ValidationError as e:
            messages.error(request, str(e))
        except PermissionDenied as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error cancelling session: {str(e)}')
    
    return render(request, 'video_chat/cancel_session.html', {
        'session': session,
        'page_title': f'Cancel {session.title}'
    })


@login_required
def download_calendar(request, session_id):
    """
    View for downloading session as calendar entry (.ics file).
    Requirements: 5.2
    """
    try:
        session = VideoSessionService.get_session(session_id)
    except VideoSession.DoesNotExist:
        messages.error(request, 'Session not found')
        return redirect('video_chat:session_list')
    
    # Check if user has access to this session
    is_host = session.host == request.user
    is_participant = VideoSessionParticipant.objects.filter(
        session=session,
        user=request.user
    ).exists()
    
    if not (is_host or is_participant):
        messages.error(request, 'You do not have access to this session')
        return redirect('video_chat:session_list')
    
    # Generate calendar entry
    from .notifications import VideoSessionNotificationService
    from django.http import HttpResponse
    
    ical_content = VideoSessionNotificationService.generate_calendar_entry(session)
    
    if not ical_content:
        messages.error(request, 'Cannot generate calendar entry for this session')
        return redirect('video_chat:session_detail', session_id=session_id)
    
    # Return as downloadable file
    response = HttpResponse(ical_content, content_type='text/calendar')
    response['Content-Disposition'] = f'attachment; filename="session_{session.session_id}.ics"'
    
    return response


@login_required
def join_session(request, session_id):
    """
    View for joining a video session.
    Requirements: 4.1, 4.2, 5.4
    """
    try:
        session = VideoSessionService.get_session(session_id)
    except VideoSession.DoesNotExist:
        messages.error(request, 'Session not found')
        return redirect('video_chat:session_list')
    
    # Check if user can join
    now = timezone.now()
    
    if session.status == 'completed':
        messages.error(request, 'This session has ended')
        return redirect('video_chat:session_detail', session_id=session_id)
    
    if session.status == 'cancelled':
        messages.error(request, 'This session has been cancelled')
        return redirect('video_chat:session_detail', session_id=session_id)
    
    # Check early join for scheduled sessions
    if session.status == 'scheduled' and session.scheduled_time:
        early_join_time = session.scheduled_time - timedelta(minutes=10)
        
        if now < early_join_time:
            minutes_until_join = int((early_join_time - now).total_seconds() / 60)
            messages.warning(
                request,
                f'You can join this session {minutes_until_join} minutes before the scheduled time'
            )
            return redirect('video_chat:session_detail', session_id=session_id)
    
    # Try to join the session
    try:
        participant = VideoSessionService.join_session(session_id, request.user)
        
        # If session is scheduled but not started, start it when host joins
        if session.status == 'scheduled' and session.host == request.user:
            VideoSessionService.start_session(session_id, request.user)
            session.refresh_from_db()
            
            # Send session started notification to participants
            from .notifications import VideoSessionNotificationService
            VideoSessionNotificationService.send_session_started_notification(session)
        
        # Redirect to video call room
        return render(request, 'video_chat/video_call_room.html', {
            'session': session,
            'participant': participant,
            'page_title': session.title
        })
        
    except ValidationError as e:
        messages.error(request, str(e))
        return redirect('video_chat:session_detail', session_id=session_id)
    except PermissionDenied as e:
        messages.error(request, str(e))
        return redirect('video_chat:session_list')
    except Exception as e:
        messages.error(request, f'Error joining session: {str(e)}')
        return redirect('video_chat:session_detail', session_id=session_id)



# ============================================================================
# REST API Endpoints
# ============================================================================

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json


@login_required
@require_http_methods(["GET"])
def api_session_list(request):
    """
    REST API endpoint to list user's video sessions.
    Requirements: 1.1, 5.1
    
    Query Parameters:
        - status: Filter by status (scheduled, active, completed, cancelled)
        - limit: Number of results to return (default: 50)
        - offset: Pagination offset (default: 0)
    
    Returns:
        JSON response with list of sessions
    """
    try:
        status_filter = request.GET.get('status')
        limit = int(request.GET.get('limit', 50))
        offset = int(request.GET.get('offset', 0))
        
        # Get user's sessions
        if status_filter:
            sessions = VideoSessionService.get_user_sessions(request.user, status=status_filter)
        else:
            sessions = VideoSessionService.get_user_sessions(request.user)
        
        # Apply pagination
        total_count = sessions.count()
        sessions = sessions[offset:offset + limit]
        
        # Serialize sessions
        sessions_data = []
        for session in sessions:
            is_host = session.host == request.user
            participant_count = session.participants.count()
            
            sessions_data.append({
                'session_id': str(session.session_id),
                'title': session.title,
                'description': session.description,
                'session_type': session.session_type,
                'status': session.status,
                'scheduled_time': session.scheduled_time.isoformat() if session.scheduled_time else None,
                'started_at': session.started_at.isoformat() if session.started_at else None,
                'ended_at': session.ended_at.isoformat() if session.ended_at else None,
                'duration_minutes': session.duration_minutes,
                'is_host': is_host,
                'host_username': session.host.username,
                'participant_count': participant_count,
                'max_participants': session.max_participants,
                'is_recorded': session.is_recorded,
                'recording_url': session.recording_url if session.recording_url else None,
                'allow_screen_share': session.allow_screen_share,
                'created_at': session.created_at.isoformat(),
            })
        
        return JsonResponse({
            'success': True,
            'sessions': sessions_data,
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        logger.error(f"Error in api_session_list: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_create_session(request):
    """
    REST API endpoint to create a new video session.
    Requirements: 1.1, 5.1
    
    Request Body (JSON):
        - session_type: Type of session (one_on_one, group, class)
        - title: Session title
        - description: Optional description
        - scheduled_time: ISO format datetime (optional)
        - duration_minutes: Duration in minutes (default: 60)
        - max_participants: Maximum participants (default: 30)
        - allow_screen_share: Boolean (default: true)
        - require_approval: Boolean (default: false)
        - participant_ids: List of user IDs to invite
    
    Returns:
        JSON response with created session details
    """
    try:
        data = json.loads(request.body)
        
        # Extract session parameters
        session_type = data.get('session_type')
        title = data.get('title')
        description = data.get('description', '')
        scheduled_time_str = data.get('scheduled_time')
        duration_minutes = data.get('duration_minutes', 60)
        max_participants = data.get('max_participants', 30)
        allow_screen_share = data.get('allow_screen_share', True)
        require_approval = data.get('require_approval', False)
        participant_ids = data.get('participant_ids', [])
        
        # Validate required fields
        if not session_type or not title:
            return JsonResponse({
                'success': False,
                'error': 'session_type and title are required'
            }, status=400)
        
        # Parse scheduled time if provided
        scheduled_time = None
        if scheduled_time_str:
            from dateutil import parser
            scheduled_time = parser.isoparse(scheduled_time_str)
        
        # Create the session
        session = VideoSessionService.create_session(
            host=request.user,
            session_type=session_type,
            title=title,
            description=description,
            scheduled_time=scheduled_time,
            duration_minutes=duration_minutes,
            max_participants=max_participants,
            allow_screen_share=allow_screen_share,
            require_approval=require_approval
        )
        
        # Add participants
        if participant_ids:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            participants = User.objects.filter(id__in=participant_ids)
            
            for participant_user in participants:
                VideoSessionParticipant.objects.create(
                    session=session,
                    user=participant_user,
                    role='participant',
                    status='invited'
                )
            
            # Send notifications
            from .notifications import VideoSessionNotificationService
            VideoSessionNotificationService.send_session_scheduled_notification(
                session, list(participants)
            )
        
        return JsonResponse({
            'success': True,
            'session': {
                'session_id': str(session.session_id),
                'title': session.title,
                'description': session.description,
                'session_type': session.session_type,
                'status': session.status,
                'scheduled_time': session.scheduled_time.isoformat() if session.scheduled_time else None,
                'duration_minutes': session.duration_minutes,
                'max_participants': session.max_participants,
                'allow_screen_share': session.allow_screen_share,
                'created_at': session.created_at.isoformat(),
            }
        }, status=201)
        
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except PermissionDenied as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=403)
    except Exception as e:
        logger.error(f"Error in api_create_session: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_session_detail(request, session_id):
    """
    REST API endpoint to get session details.
    Requirements: 1.1, 5.1
    
    Returns:
        JSON response with session details
    """
    try:
        session = VideoSessionService.get_session(session_id)
        
        # Check if user has access
        is_host = session.host == request.user
        is_participant = VideoSessionParticipant.objects.filter(
            session=session,
            user=request.user
        ).exists()
        
        if not (is_host or is_participant):
            return JsonResponse({
                'success': False,
                'error': 'You do not have access to this session'
            }, status=403)
        
        # Get participants
        participants = session.participants.select_related('user').all()
        participants_data = []
        
        for participant in participants:
            participants_data.append({
                'user_id': participant.user.id,
                'username': participant.user.username,
                'role': participant.role,
                'status': participant.status,
                'joined_at': participant.joined_at.isoformat() if participant.joined_at else None,
                'left_at': participant.left_at.isoformat() if participant.left_at else None,
                'audio_enabled': participant.audio_enabled,
                'video_enabled': participant.video_enabled,
                'screen_sharing': participant.screen_sharing,
                'connection_quality': participant.connection_quality,
            })
        
        return JsonResponse({
            'success': True,
            'session': {
                'session_id': str(session.session_id),
                'title': session.title,
                'description': session.description,
                'session_type': session.session_type,
                'status': session.status,
                'scheduled_time': session.scheduled_time.isoformat() if session.scheduled_time else None,
                'started_at': session.started_at.isoformat() if session.started_at else None,
                'ended_at': session.ended_at.isoformat() if session.ended_at else None,
                'duration_minutes': session.duration_minutes,
                'host_id': session.host.id,
                'host_username': session.host.username,
                'is_host': is_host,
                'is_participant': is_participant,
                'max_participants': session.max_participants,
                'is_recorded': session.is_recorded,
                'recording_url': session.recording_url if session.recording_url else None,
                'allow_screen_share': session.allow_screen_share,
                'require_approval': session.require_approval,
                'participants': participants_data,
                'created_at': session.created_at.isoformat(),
            }
        })
        
    except VideoSession.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Session not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error in api_session_detail: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_start_session(request, session_id):
    """
    REST API endpoint to start a video session.
    Requirements: 1.1, 5.1
    
    Returns:
        JSON response with updated session status
    """
    try:
        VideoSessionService.start_session(session_id, request.user)
        session = VideoSessionService.get_session(session_id)
        
        # Send notifications
        from .notifications import VideoSessionNotificationService
        VideoSessionNotificationService.send_session_started_notification(session)
        
        return JsonResponse({
            'success': True,
            'session': {
                'session_id': str(session.session_id),
                'status': session.status,
                'started_at': session.started_at.isoformat() if session.started_at else None,
            }
        })
        
    except VideoSession.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Session not found'
        }, status=404)
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except PermissionDenied as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=403)
    except Exception as e:
        logger.error(f"Error in api_start_session: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_end_session(request, session_id):
    """
    REST API endpoint to end a video session.
    Requirements: 1.1, 5.2
    
    Returns:
        JSON response with updated session status
    """
    try:
        VideoSessionService.end_session(session_id, request.user)
        session = VideoSessionService.get_session(session_id)
        
        return JsonResponse({
            'success': True,
            'session': {
                'session_id': str(session.session_id),
                'status': session.status,
                'ended_at': session.ended_at.isoformat() if session.ended_at else None,
            }
        })
        
    except VideoSession.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Session not found'
        }, status=404)
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except PermissionDenied as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=403)
    except Exception as e:
        logger.error(f"Error in api_end_session: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_join_session(request, session_id):
    """
    REST API endpoint to join a video session.
    Requirements: 4.1, 4.2
    
    Returns:
        JSON response with participant details
    """
    try:
        participant = VideoSessionService.join_session(session_id, request.user)
        session = VideoSessionService.get_session(session_id)
        
        # If session is scheduled but not started, start it when host joins
        if session.status == 'scheduled' and session.host == request.user:
            VideoSessionService.start_session(session_id, request.user)
            session.refresh_from_db()
            
            # Send session started notification
            from .notifications import VideoSessionNotificationService
            VideoSessionNotificationService.send_session_started_notification(session)
        
        return JsonResponse({
            'success': True,
            'participant': {
                'user_id': participant.user.id,
                'username': participant.user.username,
                'role': participant.role,
                'status': participant.status,
                'joined_at': participant.joined_at.isoformat() if participant.joined_at else None,
            },
            'session': {
                'session_id': str(session.session_id),
                'status': session.status,
                'title': session.title,
            }
        })
        
    except VideoSession.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Session not found'
        }, status=404)
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except PermissionDenied as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=403)
    except Exception as e:
        logger.error(f"Error in api_join_session: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_leave_session(request, session_id):
    """
    REST API endpoint to leave a video session.
    Requirements: 4.1
    
    Returns:
        JSON response confirming leave
    """
    try:
        VideoSessionService.leave_session(session_id, request.user)
        
        return JsonResponse({
            'success': True,
            'message': 'Successfully left the session'
        })
        
    except VideoSession.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Session not found'
        }, status=404)
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Error in api_leave_session: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_session_participants(request, session_id):
    """
    REST API endpoint to get session participants.
    Requirements: 1.1, 4.1
    
    Returns:
        JSON response with list of participants
    """
    try:
        session = VideoSessionService.get_session(session_id)
        
        # Check if user has access
        is_host = session.host == request.user
        is_participant = VideoSessionParticipant.objects.filter(
            session=session,
            user=request.user
        ).exists()
        
        if not (is_host or is_participant):
            return JsonResponse({
                'success': False,
                'error': 'You do not have access to this session'
            }, status=403)
        
        # Get participants
        participants = session.participants.select_related('user').all()
        participants_data = []
        
        for participant in participants:
            participants_data.append({
                'user_id': participant.user.id,
                'username': participant.user.username,
                'role': participant.role,
                'status': participant.status,
                'joined_at': participant.joined_at.isoformat() if participant.joined_at else None,
                'left_at': participant.left_at.isoformat() if participant.left_at else None,
                'audio_enabled': participant.audio_enabled,
                'video_enabled': participant.video_enabled,
                'screen_sharing': participant.screen_sharing,
                'connection_quality': participant.connection_quality,
            })
        
        return JsonResponse({
            'success': True,
            'participants': participants_data,
            'total_count': len(participants_data)
        })
        
    except VideoSession.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Session not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error in api_session_participants: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_update_media_state(request, session_id):
    """
    REST API endpoint to update participant's media state.
    Requirements: 1.5, 7.1, 7.2, 7.3
    
    Request Body (JSON):
        - audio_enabled: Boolean
        - video_enabled: Boolean
    
    Returns:
        JSON response confirming update
    """
    try:
        data = json.loads(request.body)
        audio_enabled = data.get('audio_enabled')
        video_enabled = data.get('video_enabled')
        
        VideoSessionService.update_participant_media_state(
            session_id,
            request.user,
            audio_enabled=audio_enabled,
            video_enabled=video_enabled
        )
        
        return JsonResponse({
            'success': True,
            'media_state': {
                'audio_enabled': audio_enabled,
                'video_enabled': video_enabled
            }
        })
        
    except VideoSession.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Session not found'
        }, status=404)
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Error in api_update_media_state: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_start_recording(request, session_id):
    """
    REST API endpoint to start session recording.
    Requirements: 6.1, 6.2
    
    Returns:
        JSON response confirming recording started
    """
    try:
        VideoSessionService.start_recording(session_id, request.user)
        
        return JsonResponse({
            'success': True,
            'message': 'Recording started successfully'
        })
        
    except VideoSession.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Session not found'
        }, status=404)
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except PermissionDenied as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=403)
    except Exception as e:
        logger.error(f"Error in api_start_recording: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_stop_recording(request, session_id):
    """
    REST API endpoint to stop session recording.
    Requirements: 6.4, 6.5
    
    Returns:
        JSON response with recording details
    """
    try:
        recording_url = VideoSessionService.stop_recording(session_id, request.user)
        
        return JsonResponse({
            'success': True,
            'message': 'Recording stopped successfully',
            'recording_url': recording_url if recording_url else None
        })
        
    except VideoSession.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Session not found'
        }, status=404)
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except PermissionDenied as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=403)
    except Exception as e:
        logger.error(f"Error in api_stop_recording: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_session_statistics(request, session_id):
    """
    REST API endpoint to get session statistics.
    Requirements: 8.1, 8.2, 8.3
    
    Returns:
        JSON response with session statistics
    """
    try:
        session = VideoSessionService.get_session(session_id)
        
        # Check if user has access
        is_host = session.host == request.user
        is_participant = VideoSessionParticipant.objects.filter(
            session=session,
            user=request.user
        ).exists()
        
        if not (is_host or is_participant):
            return JsonResponse({
                'success': False,
                'error': 'You do not have access to this session'
            }, status=403)
        
        # Get statistics
        statistics = VideoSessionService.get_session_statistics(session_id)
        
        return JsonResponse({
            'success': True,
            'statistics': statistics
        })
        
    except VideoSession.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Session not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error in api_session_statistics: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
