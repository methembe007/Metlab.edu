from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from accounts.decorators import role_required
from accounts.models import StudentProfile
from .models import (TutorProfile, Subject, TutorBooking, TutorReview, TutorAvailability,
                     StudyPartnerRequest, StudyPartnership, StudySession, StudyGroup, 
                     StudyGroupMembership, StudyGroupMessage, StudySessionAttendance)
import json


@login_required
@role_required('student')
def tutor_recommendations(request):
    """View to display AI-powered tutor recommendations for students"""
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found. Please complete your profile setup.")
        return redirect('accounts:student_dashboard')
    
    # Get filter parameters
    subject_filter = request.GET.get('subject')
    experience_filter = request.GET.get('experience')
    min_rating = request.GET.get('min_rating', 0)
    max_rate = request.GET.get('max_rate')
    
    # Get active tutors
    tutors = TutorProfile.objects.filter(
        status='active',
        verified=True
    ).select_related('user').prefetch_related('subjects', 'reviews')
    
    # Apply filters
    if subject_filter:
        tutors = tutors.filter(subjects__name=subject_filter)
    
    if experience_filter:
        tutors = tutors.filter(experience_level=experience_filter)
    
    if min_rating:
        tutors = tutors.filter(rating__gte=float(min_rating))
    
    if max_rate:
        tutors = tutors.filter(hourly_rate__lte=float(max_rate))
    
    # Calculate compatibility scores and sort
    tutor_scores = []
    for tutor in tutors:
        compatibility_score = tutor.get_compatibility_score(student)
        tutor_scores.append({
            'tutor': tutor,
            'compatibility_score': compatibility_score
        })
    
    # Sort by compatibility score (highest first)
    tutor_scores.sort(key=lambda x: x['compatibility_score'], reverse=True)
    
    # Paginate results
    paginator = Paginator(tutor_scores, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    subjects = Subject.objects.all().order_by('name')
    experience_levels = TutorProfile.EXPERIENCE_LEVEL_CHOICES
    
    context = {
        'page_obj': page_obj,
        'subjects': subjects,
        'experience_levels': experience_levels,
        'current_filters': {
            'subject': subject_filter,
            'experience': experience_filter,
            'min_rating': min_rating,
            'max_rate': max_rate,
        }
    }
    
    return render(request, 'community/tutor_recommendations.html', context)


@login_required
@role_required('student')
def tutor_detail(request, tutor_id):
    """View to display detailed information about a specific tutor"""
    tutor = get_object_or_404(TutorProfile, id=tutor_id, status='active', verified=True)
    
    try:
        student = request.user.student_profile
        compatibility_score = tutor.get_compatibility_score(student)
    except StudentProfile.DoesNotExist:
        compatibility_score = 0
    
    # Get recent reviews
    reviews = tutor.reviews.select_related('student__user').order_by('-created_at')[:10]
    
    # Get availability for the next 7 days
    today = timezone.now().date()
    availability_data = []
    
    for i in range(7):
        date = today + timedelta(days=i)
        weekday = date.weekday()
        
        # Get availability slots for this day
        slots = tutor.availability_slots.filter(
            day_of_week=weekday,
            is_available=True
        ).order_by('start_time')
        
        # Filter out booked slots
        available_slots = []
        for slot in slots:
            slot_datetime = datetime.combine(date, slot.start_time)
            if tutor.is_available_at(slot_datetime):
                available_slots.append({
                    'start_time': slot.start_time,
                    'end_time': slot.end_time,
                    'datetime': slot_datetime
                })
        
        availability_data.append({
            'date': date,
            'weekday': date.strftime('%A'),
            'slots': available_slots
        })
    
    context = {
        'tutor': tutor,
        'compatibility_score': compatibility_score,
        'reviews': reviews,
        'availability_data': availability_data,
    }
    
    return render(request, 'community/tutor_detail.html', context)


@login_required
@role_required('student')
def book_tutor(request, tutor_id):
    """View to book a tutoring session"""
    tutor = get_object_or_404(TutorProfile, id=tutor_id, status='active', verified=True)
    
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('accounts:student_dashboard')
    
    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        scheduled_time_str = request.POST.get('scheduled_time')
        duration = int(request.POST.get('duration', 60))
        notes = request.POST.get('notes', '')
        
        try:
            subject = Subject.objects.get(id=subject_id)
            scheduled_time = datetime.fromisoformat(scheduled_time_str.replace('Z', '+00:00'))
            
            # Check if tutor is available at this time
            if not tutor.is_available_at(scheduled_time):
                messages.error(request, "The selected time slot is no longer available.")
                return redirect('community:tutor_detail', tutor_id=tutor.id)
            
            # Create booking
            booking = TutorBooking.objects.create(
                tutor=tutor,
                student=student,
                subject=subject,
                scheduled_time=scheduled_time,
                duration_minutes=duration,
                notes=notes
            )
            
            messages.success(request, f"Booking request sent to {tutor.user.get_full_name() or tutor.user.username}!")
            return redirect('community:booking_detail', booking_id=booking.id)
            
        except (Subject.DoesNotExist, ValueError) as e:
            messages.error(request, "Invalid booking data. Please try again.")
            return redirect('community:tutor_detail', tutor_id=tutor.id)
    
    # GET request - show booking form
    subjects = tutor.subjects.all()
    
    context = {
        'tutor': tutor,
        'subjects': subjects,
    }
    
    return render(request, 'community/book_tutor.html', context)


@login_required
@role_required('student')
def booking_detail(request, booking_id):
    """View to display booking details"""
    booking = get_object_or_404(
        TutorBooking,
        id=booking_id,
        student__user=request.user
    )
    
    context = {
        'booking': booking,
    }
    
    return render(request, 'community/booking_detail.html', context)


@login_required
@role_required('student')
def my_bookings(request):
    """View to display student's bookings"""
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('accounts:student_dashboard')
    
    # Get bookings with filters
    status_filter = request.GET.get('status', 'all')
    
    bookings = student.tutor_bookings.select_related(
        'tutor__user', 'subject'
    ).order_by('-scheduled_time')
    
    if status_filter != 'all':
        bookings = bookings.filter(status=status_filter)
    
    # Paginate results
    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'status_choices': TutorBooking.STATUS_CHOICES,
    }
    
    return render(request, 'community/my_bookings.html', context)


@login_required
@role_required('student')
def cancel_booking(request, booking_id):
    """View to cancel a booking"""
    booking = get_object_or_404(
        TutorBooking,
        id=booking_id,
        student__user=request.user,
        status__in=['pending', 'confirmed']
    )
    
    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.save()
        messages.success(request, "Booking cancelled successfully.")
        return redirect('community:my_bookings')
    
    context = {
        'booking': booking,
    }
    
    return render(request, 'community/cancel_booking.html', context)


@login_required
@role_required('student')
def review_tutor(request, booking_id):
    """View to review a tutor after a completed session"""
    booking = get_object_or_404(
        TutorBooking,
        id=booking_id,
        student__user=request.user,
        status='completed'
    )
    
    # Check if review already exists
    if hasattr(booking, 'review'):
        messages.info(request, "You have already reviewed this session.")
        return redirect('community:booking_detail', booking_id=booking.id)
    
    if request.method == 'POST':
        rating = int(request.POST.get('rating'))
        comment = request.POST.get('comment')
        would_recommend = request.POST.get('would_recommend') == 'on'
        
        # Create review
        TutorReview.objects.create(
            tutor=booking.tutor,
            student=booking.student,
            booking=booking,
            rating=rating,
            comment=comment,
            would_recommend=would_recommend
        )
        
        messages.success(request, "Thank you for your review!")
        return redirect('community:booking_detail', booking_id=booking.id)
    
    context = {
        'booking': booking,
    }
    
    return render(request, 'community/review_tutor.html', context)


@login_required
def tutor_search_api(request):
    """API endpoint for tutor search with autocomplete"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'tutors': []})
    
    tutors = TutorProfile.objects.filter(
        Q(user__first_name__icontains=query) |
        Q(user__last_name__icontains=query) |
        Q(user__username__icontains=query) |
        Q(subjects__name__icontains=query),
        status='active',
        verified=True
    ).select_related('user').prefetch_related('subjects').distinct()[:10]
    
    tutor_data = []
    for tutor in tutors:
        tutor_data.append({
            'id': tutor.id,
            'name': tutor.user.get_full_name() or tutor.user.username,
            'subjects': [subject.name for subject in tutor.subjects.all()],
            'rating': tutor.rating,
            'hourly_rate': float(tutor.hourly_rate),
        })
    
    return JsonResponse({'tutors': tutor_data})


# Study Partner Views

@login_required
@role_required('student')
def study_partner_recommendations(request):
    """View to display AI-powered study partner recommendations"""
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found. Please complete your profile setup.")
        return redirect('accounts:student_dashboard')
    
    from .partner_services import StudyPartnerMatcher
    
    # Get filter parameters
    subject_filter = request.GET.get('subject')
    
    matcher = StudyPartnerMatcher()
    
    # Get subject for filtering if specified
    subject_obj = None
    if subject_filter:
        try:
            subject_obj = Subject.objects.get(name=subject_filter)
        except Subject.DoesNotExist:
            subject_obj = None
    
    # Get recommendations
    recommendations = matcher.get_partner_recommendations(
        student, 
        subject=subject_obj, 
        limit=20
    )
    
    # Paginate results
    paginator = Paginator(recommendations, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options (subjects the student is interested in)
    subjects = Subject.objects.filter(
        name__in=student.subjects_of_interest
    ).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'subjects': subjects,
        'current_subject': subject_filter,
        'student': student,
    }
    
    return render(request, 'community/study_partner_recommendations.html', context)


@login_required
@role_required('student')
def send_partner_request(request):
    """View to send a study partner request"""
    if request.method != 'POST':
        return redirect('community:study_partner_recommendations')
    
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('accounts:student_dashboard')
    
    from .partner_services import StudyPartnerService
    
    partner_id = request.POST.get('partner_id')
    subject_id = request.POST.get('subject_id')
    message = request.POST.get('message', '')
    
    try:
        partner = StudentProfile.objects.get(id=partner_id)
        subject = Subject.objects.get(id=subject_id)
        
        service = StudyPartnerService()
        partner_request = service.send_partner_request(
            requester=student,
            requested=partner,
            subject=subject,
            message=message
        )
        
        if partner_request:
            messages.success(request, f"Partner request sent to {partner.user.get_full_name() or partner.user.username}!")
        else:
            messages.warning(request, "A request or partnership already exists with this student.")
            
    except (StudentProfile.DoesNotExist, Subject.DoesNotExist):
        messages.error(request, "Invalid request data.")
    
    return redirect('community:study_partner_recommendations')


@login_required
@role_required('student')
def partner_requests(request):
    """View to display received and sent partner requests"""
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('accounts:student_dashboard')
    
    from .partner_services import StudyPartnerService
    
    service = StudyPartnerService()
    
    # Get received and sent requests
    received_requests = service.get_student_requests(student, 'received')
    sent_requests = service.get_student_requests(student, 'sent')
    
    context = {
        'received_requests': received_requests,
        'sent_requests': sent_requests,
    }
    
    return render(request, 'community/partner_requests.html', context)


@login_required
@role_required('student')
def respond_to_partner_request(request, request_id):
    """View to accept or decline a partner request"""
    if request.method != 'POST':
        return redirect('community:partner_requests')
    
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('accounts:student_dashboard')
    
    from .models import StudyPartnerRequest
    from .partner_services import StudyPartnerService
    
    partner_request = get_object_or_404(
        StudyPartnerRequest,
        id=request_id,
        requested=student,
        status='pending'
    )
    
    action = request.POST.get('action')
    service = StudyPartnerService()
    
    if action == 'accept':
        try:
            partnership = service.accept_partner_request(partner_request)
            messages.success(request, f"You are now study partners with {partner_request.requester.user.get_full_name() or partner_request.requester.user.username}!")
        except ValueError as e:
            messages.error(request, str(e))
    elif action == 'decline':
        try:
            service.decline_partner_request(partner_request)
            messages.info(request, "Partner request declined.")
        except ValueError as e:
            messages.error(request, str(e))
    
    return redirect('community:partner_requests')


@login_required
@role_required('student')
def cancel_partner_request(request, request_id):
    """View to cancel a sent partner request"""
    if request.method != 'POST':
        return redirect('community:partner_requests')
    
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('accounts:student_dashboard')
    
    from .models import StudyPartnerRequest
    from .partner_services import StudyPartnerService
    
    partner_request = get_object_or_404(
        StudyPartnerRequest,
        id=request_id,
        requester=student,
        status='pending'
    )
    
    service = StudyPartnerService()
    
    try:
        service.cancel_partner_request(partner_request)
        messages.info(request, "Partner request cancelled.")
    except ValueError as e:
        messages.error(request, str(e))
    
    return redirect('community:partner_requests')


@login_required
@role_required('student')
def my_study_partners(request):
    """View to display student's active study partnerships"""
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('accounts:student_dashboard')
    
    from .partner_services import StudyPartnerService
    
    service = StudyPartnerService()
    partnerships = service.get_student_partnerships(student, status='active')
    
    # Get upcoming study sessions
    from .models import StudySession
    upcoming_sessions = StudySession.objects.filter(
        partnership__in=partnerships,
        scheduled_time__gte=timezone.now(),
        status='scheduled'
    ).select_related('partnership__student1__user', 'partnership__student2__user', 'partnership__subject').order_by('scheduled_time')[:5]
    
    context = {
        'partnerships': partnerships,
        'upcoming_sessions': upcoming_sessions,
        'student': student,
    }
    
    return render(request, 'community/my_study_partners.html', context)


@login_required
@role_required('student')
def schedule_study_session(request, partnership_id):
    """View to schedule a study session with a partner"""
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('accounts:student_dashboard')
    
    from .models import StudyPartnership
    from .partner_services import StudyPartnerService
    
    partnership = get_object_or_404(
        StudyPartnership,
        id=partnership_id,
        status='active'
    )
    
    # Verify student is part of this partnership
    if partnership.student1 != student and partnership.student2 != student:
        messages.error(request, "You are not part of this partnership.")
        return redirect('community:my_study_partners')
    
    if request.method == 'POST':
        scheduled_time_str = request.POST.get('scheduled_time')
        duration = int(request.POST.get('duration', 60))
        topic = request.POST.get('topic', '')
        notes = request.POST.get('notes', '')
        
        try:
            scheduled_time = datetime.fromisoformat(scheduled_time_str.replace('Z', '+00:00'))
            
            service = StudyPartnerService()
            session = service.schedule_study_session(
                partnership=partnership,
                scheduled_time=scheduled_time,
                duration_minutes=duration,
                topic=topic,
                notes=notes,
                created_by=student
            )
            
            partner = partnership.get_partner(student)
            messages.success(request, f"Study session scheduled with {partner.user.get_full_name() or partner.user.username}!")
            return redirect('community:study_session_detail', session_id=session.id)
            
        except ValueError:
            messages.error(request, "Invalid session data. Please try again.")
    
    # GET request - show scheduling form
    partner = partnership.get_partner(student)
    
    context = {
        'partnership': partnership,
        'partner': partner,
    }
    
    return render(request, 'community/schedule_study_session.html', context)


@login_required
@role_required('student')
def study_session_detail(request, session_id):
    """View to display study session details"""
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('accounts:student_dashboard')
    
    from .models import StudySession
    
    session = get_object_or_404(StudySession, id=session_id)
    
    # Verify student is part of this session's partnership
    partnership = session.partnership
    if partnership.student1 != student and partnership.student2 != student:
        messages.error(request, "You don't have access to this session.")
        return redirect('community:my_study_partners')
    
    partner = partnership.get_partner(student)
    
    context = {
        'session': session,
        'partnership': partnership,
        'partner': partner,
        'student': student,
    }
    
    return render(request, 'community/study_session_detail.html', context)


@login_required
@role_required('student')
def my_study_sessions(request):
    """View to display student's study sessions"""
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('accounts:student_dashboard')
    
    from .models import StudySession, StudyPartnership
    from .partner_services import StudyPartnerService
    
    service = StudyPartnerService()
    partnerships = service.get_student_partnerships(student, status='active')
    
    # Get sessions with filters
    status_filter = request.GET.get('status', 'all')
    
    sessions = StudySession.objects.filter(
        partnership__in=partnerships
    ).select_related(
        'partnership__student1__user', 
        'partnership__student2__user', 
        'partnership__subject'
    ).order_by('-scheduled_time')
    
    if status_filter != 'all':
        sessions = sessions.filter(status=status_filter)
    
    # Paginate results
    paginator = Paginator(sessions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'status_choices': StudySession.STATUS_CHOICES,
        'student': student,
    }
    
    return render(request, 'community/my_study_sessions.html', context)


@login_required
@role_required('student')
def study_room(request, session_id):
    """View to enter a real-time study room"""
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('accounts:student_dashboard')
    
    from .models import StudySession
    
    session = get_object_or_404(StudySession, id=session_id)
    
    # Verify student has access to this session
    has_access = False
    
    if session.session_type == 'partnership' and session.partnership:
        partnership = session.partnership
        if partnership.student1 == student or partnership.student2 == student:
            has_access = True
    elif session.session_type == 'group' and session.study_group:
        if session.study_group.is_member(student):
            has_access = True
    
    if not has_access:
        messages.error(request, "You don't have access to this study room.")
        return redirect('community:my_study_sessions')
    
    # Update session status to in_progress if it's scheduled
    if session.status == 'scheduled':
        session.status = 'in_progress'
        session.save()
    
    # Create or update attendance record
    from .models import StudySessionAttendance
    attendance, created = StudySessionAttendance.objects.get_or_create(
        session=session,
        student=student,
        defaults={'status': 'confirmed', 'joined_at': timezone.now()}
    )
    
    if not created and not attendance.joined_at:
        attendance.joined_at = timezone.now()
        attendance.status = 'attended'
        attendance.save()
    
    context = {
        'session': session,
        'student': student,
    }
    
    return render(request, 'community/study_room.html', context)


@login_required
def study_room_js(request):
    """Serve the study room JavaScript file"""
    from django.http import FileResponse
    import os
    from django.conf import settings
    
    js_path = os.path.join(settings.STATICFILES_DIRS[0], 'js', 'study_room.js')
    return FileResponse(open(js_path, 'rb'), content_type='application/javascript')


@login_required
@role_required('student')
def report_study_room_issue(request):
    """API endpoint to report issues in study rooms"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return JsonResponse({'error': 'Student profile not found'}, status=400)
    
    import json
    data = json.loads(request.body)
    
    session_id = data.get('sessionId')
    issue_type = data.get('issueType')
    description = data.get('description')
    
    if not all([session_id, issue_type, description]):
        return JsonResponse({'error': 'Missing required fields'}, status=400)
    
    from .models import StudySession, StudyRoomReport
    
    try:
        session = StudySession.objects.get(id=session_id)
        
        # Create report record
        report = StudyRoomReport.objects.create(
            session=session,
            reporter=student,
            issue_type=issue_type,
            description=description,
            status='pending'
        )
        
        # TODO: Send notification to moderators
        
        return JsonResponse({'success': True, 'reportId': report.id})
        
    except StudySession.DoesNotExist:
        return JsonResponse({'error': 'Session not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': 'Failed to submit report'}, status=500)


# Study Group Views

@login_required
@role_required('student')
def study_groups(request):
    """View to display available study groups and allow searching/filtering"""
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found. Please complete your profile setup.")
        return redirect('accounts:student_dashboard')
    
    # Get filter parameters
    subject_filter = request.GET.get('subject')
    search_query = request.GET.get('search', '').strip()
    
    # Get active public study groups
    groups = StudyGroup.objects.filter(
        status='active',
        is_public=True
    ).select_related('subject', 'created_by__user').prefetch_related('memberships')
    
    # Apply filters
    if subject_filter:
        groups = groups.filter(subject__name=subject_filter)
    
    if search_query:
        groups = groups.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Exclude groups where student is already a member
    student_group_ids = StudyGroupMembership.objects.filter(
        student=student,
        status='active'
    ).values_list('study_group_id', flat=True)
    
    groups = groups.exclude(id__in=student_group_ids)
    
    # Annotate with member count
    from django.db.models import Count
    groups = groups.annotate(
        member_count=Count('memberships', filter=Q(memberships__status='active'))
    ).order_by('-created_at')
    
    # Paginate results
    paginator = Paginator(groups, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options (subjects the student is interested in)
    subjects = Subject.objects.filter(
        name__in=student.subjects_of_interest
    ).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'subjects': subjects,
        'current_filters': {
            'subject': subject_filter,
            'search': search_query,
        },
        'student': student,
    }
    
    return render(request, 'community/study_groups.html', context)


@login_required
@role_required('student')
def create_study_group(request):
    """View to create a new study group"""
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('accounts:student_dashboard')
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        subject_id = request.POST.get('subject')
        max_members = int(request.POST.get('max_members', 6))
        is_public = request.POST.get('is_public') == 'on'
        requires_approval = request.POST.get('requires_approval') == 'on'
        
        if not name:
            messages.error(request, "Group name is required.")
            return render(request, 'community/create_study_group.html', {
                'subjects': Subject.objects.all().order_by('name')
            })
        
        try:
            subject = Subject.objects.get(id=subject_id)
            
            # Create the study group
            study_group = StudyGroup.objects.create(
                name=name,
                description=description,
                subject=subject,
                created_by=student,
                max_members=max_members,
                is_public=is_public,
                requires_approval=requires_approval
            )
            
            # Add creator as admin member
            StudyGroupMembership.objects.create(
                study_group=study_group,
                student=student,
                role='admin',
                status='active'
            )
            
            # Create system message for group creation
            StudyGroupMessage.objects.create(
                study_group=study_group,
                message_type='system',
                content=f"Study group '{name}' was created by {student.user.get_full_name() or student.user.username}"
            )
            
            messages.success(request, f"Study group '{name}' created successfully!")
            return redirect('community:study_group_detail', group_id=study_group.id)
            
        except Subject.DoesNotExist:
            messages.error(request, "Invalid subject selected.")
        except Exception as e:
            messages.error(request, "Error creating study group. Please try again.")
    
    # GET request - show creation form
    subjects = Subject.objects.all().order_by('name')
    
    context = {
        'subjects': subjects,
    }
    
    return render(request, 'community/create_study_group.html', context)


@login_required
@role_required('student')
def study_group_detail(request, group_id):
    """View to display study group details and chat"""
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('accounts:student_dashboard')
    
    study_group = get_object_or_404(StudyGroup, id=group_id)
    
    # Check if student is a member
    try:
        membership = StudyGroupMembership.objects.get(
            study_group=study_group,
            student=student,
            status='active'
        )
        is_member = True
    except StudyGroupMembership.DoesNotExist:
        membership = None
        is_member = False
    
    # If not a member and group is not public, deny access
    if not is_member and not study_group.is_public:
        messages.error(request, "You don't have access to this study group.")
        return redirect('community:study_groups')
    
    # Get group members
    members = StudyGroupMembership.objects.filter(
        study_group=study_group,
        status='active'
    ).select_related('student__user').order_by('role', 'joined_at')
    
    # Get recent messages (last 50)
    messages_list = StudyGroupMessage.objects.filter(
        study_group=study_group
    ).select_related('sender__user').order_by('-created_at')[:50]
    messages_list = list(reversed(messages_list))  # Show oldest first
    
    # Get upcoming group sessions
    upcoming_sessions = StudySession.objects.filter(
        study_group=study_group,
        scheduled_time__gte=timezone.now(),
        status='scheduled'
    ).order_by('scheduled_time')[:5]
    
    context = {
        'study_group': study_group,
        'membership': membership,
        'is_member': is_member,
        'members': members,
        'messages': messages_list,
        'upcoming_sessions': upcoming_sessions,
        'can_join': study_group.can_join() and not is_member,
    }
    
    return render(request, 'community/study_group_detail.html', context)


@login_required
@role_required('student')
def join_study_group(request, group_id):
    """View to join a study group"""
    if request.method != 'POST':
        return redirect('community:study_groups')
    
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('accounts:student_dashboard')
    
    study_group = get_object_or_404(StudyGroup, id=group_id, status='active')
    
    # Check if student is already a member
    if study_group.is_member(student):
        messages.warning(request, "You are already a member of this group.")
        return redirect('community:study_group_detail', group_id=group_id)
    
    # Check if group can accept new members
    if not study_group.can_join():
        messages.error(request, "This group is full or not accepting new members.")
        return redirect('community:study_groups')
    
    # Create membership
    status = 'pending' if study_group.requires_approval else 'active'
    
    StudyGroupMembership.objects.create(
        study_group=study_group,
        student=student,
        status=status
    )
    
    # Create system message
    if status == 'active':
        StudyGroupMessage.objects.create(
            study_group=study_group,
            message_type='system',
            content=f"{student.user.get_full_name() or student.user.username} joined the group"
        )
        messages.success(request, f"You have joined '{study_group.name}'!")
    else:
        messages.info(request, f"Your request to join '{study_group.name}' is pending approval.")
    
    return redirect('community:study_group_detail', group_id=group_id)


@login_required
@role_required('student')
def leave_study_group(request, group_id):
    """View to leave a study group"""
    if request.method != 'POST':
        return redirect('community:my_study_groups')
    
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('accounts:student_dashboard')
    
    study_group = get_object_or_404(StudyGroup, id=group_id)
    
    try:
        membership = StudyGroupMembership.objects.get(
            study_group=study_group,
            student=student,
            status='active'
        )
        
        # Update membership status
        membership.status = 'left'
        membership.save()
        
        # Create system message
        StudyGroupMessage.objects.create(
            study_group=study_group,
            message_type='system',
            content=f"{student.user.get_full_name() or student.user.username} left the group"
        )
        
        messages.success(request, f"You have left '{study_group.name}'.")
        
    except StudyGroupMembership.DoesNotExist:
        messages.error(request, "You are not a member of this group.")
    
    return redirect('community:my_study_groups')


@login_required
@role_required('student')
def my_study_groups(request):
    """View to display student's study groups"""
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('accounts:student_dashboard')
    
    # Get student's active group memberships
    memberships = StudyGroupMembership.objects.filter(
        student=student,
        status='active'
    ).select_related('study_group__subject', 'study_group__created_by__user').order_by('-joined_at')
    
    # Get upcoming group sessions
    group_ids = [membership.study_group.id for membership in memberships]
    upcoming_sessions = StudySession.objects.filter(
        study_group_id__in=group_ids,
        scheduled_time__gte=timezone.now(),
        status='scheduled'
    ).select_related('study_group', 'created_by__user').order_by('scheduled_time')[:10]
    
    context = {
        'memberships': memberships,
        'upcoming_sessions': upcoming_sessions,
        'student': student,
    }
    
    return render(request, 'community/my_study_groups.html', context)


@login_required
@role_required('student')
def send_group_message(request, group_id):
    """API endpoint to send a message to a study group"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return JsonResponse({'error': 'Student profile not found'}, status=400)
    
    study_group = get_object_or_404(StudyGroup, id=group_id)
    
    # Check if student is an active member
    if not study_group.is_member(student):
        return JsonResponse({'error': 'Not a member of this group'}, status=403)
    
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        
        if not content:
            return JsonResponse({'error': 'Message content required'}, status=400)
        
        # Create message
        message = StudyGroupMessage.objects.create(
            study_group=study_group,
            sender=student,
            message_type='text',
            content=content
        )
        
        # Return message data
        return JsonResponse({
            'id': message.id,
            'sender': {
                'name': message.sender.user.get_full_name() or message.sender.user.username,
                'id': message.sender.id
            },
            'content': message.content,
            'created_at': message.created_at.isoformat(),
            'message_type': message.message_type
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Failed to send message'}, status=500)


@login_required
@role_required('student')
def get_group_messages(request, group_id):
    """API endpoint to get recent messages from a study group"""
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return JsonResponse({'error': 'Student profile not found'}, status=400)
    
    study_group = get_object_or_404(StudyGroup, id=group_id)
    
    # Check if student is an active member
    if not study_group.is_member(student):
        return JsonResponse({'error': 'Not a member of this group'}, status=403)
    
    # Get messages after a certain timestamp (for polling)
    after_timestamp = request.GET.get('after')
    messages_query = StudyGroupMessage.objects.filter(study_group=study_group)
    
    if after_timestamp:
        try:
            after_dt = datetime.fromisoformat(after_timestamp.replace('Z', '+00:00'))
            messages_query = messages_query.filter(created_at__gt=after_dt)
        except ValueError:
            pass
    
    messages_list = messages_query.select_related('sender__user').order_by('created_at')[:50]
    
    messages_data = []
    for message in messages_list:
        sender_data = None
        if message.sender:
            sender_data = {
                'name': message.sender.user.get_full_name() or message.sender.user.username,
                'id': message.sender.id
            }
        
        messages_data.append({
            'id': message.id,
            'sender': sender_data,
            'content': message.content,
            'created_at': message.created_at.isoformat(),
            'message_type': message.message_type
        })
    
    return JsonResponse({'messages': messages_data})


@login_required
@role_required('student')
def schedule_group_session(request, group_id):
    """View to schedule a study session for a group"""
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('accounts:student_dashboard')
    
    study_group = get_object_or_404(StudyGroup, id=group_id, status='active')
    
    # Check if student is an active member
    if not study_group.is_member(student):
        messages.error(request, "You are not a member of this group.")
        return redirect('community:study_groups')
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        scheduled_time_str = request.POST.get('scheduled_time')
        duration = int(request.POST.get('duration', 60))
        topic = request.POST.get('topic', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not title:
            messages.error(request, "Session title is required.")
            return render(request, 'community/schedule_group_session.html', {
                'study_group': study_group
            })
        
        try:
            scheduled_time = datetime.fromisoformat(scheduled_time_str.replace('Z', '+00:00'))
            
            # Create group study session
            session = StudySession.objects.create(
                study_group=study_group,
                session_type='group',
                title=title,
                scheduled_time=scheduled_time,
                duration_minutes=duration,
                topic=topic,
                description=description,
                created_by=student
            )
            
            # Create attendance records for all active members
            active_members = StudyGroupMembership.objects.filter(
                study_group=study_group,
                status='active'
            ).select_related('student')
            
            for membership in active_members:
                StudySessionAttendance.objects.create(
                    session=session,
                    student=membership.student,
                    status='invited'
                )
            
            # Create system message
            StudyGroupMessage.objects.create(
                study_group=study_group,
                message_type='system',
                content=f"{student.user.get_full_name() or student.user.username} scheduled a study session: '{title}' on {scheduled_time.strftime('%B %d, %Y at %I:%M %p')}"
            )
            
            messages.success(request, f"Study session '{title}' scheduled successfully!")
            return redirect('community:group_session_detail', session_id=session.id)
            
        except ValueError:
            messages.error(request, "Invalid session data. Please try again.")
    
    # GET request - show scheduling form
    context = {
        'study_group': study_group,
    }
    
    return render(request, 'community/schedule_group_session.html', context)


@login_required
@role_required('student')
def group_session_detail(request, session_id):
    """View to display group study session details"""
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('accounts:student_dashboard')
    
    session = get_object_or_404(StudySession, id=session_id, session_type='group')
    
    # Check if student is a member of the group
    if not session.study_group.is_member(student):
        messages.error(request, "You don't have access to this session.")
        return redirect('community:my_study_groups')
    
    # Get attendance records
    attendance_records = StudySessionAttendance.objects.filter(
        session=session
    ).select_related('student__user').order_by('student__user__first_name', 'student__user__username')
    
    # Get student's attendance record
    try:
        student_attendance = StudySessionAttendance.objects.get(
            session=session,
            student=student
        )
    except StudySessionAttendance.DoesNotExist:
        student_attendance = None
    
    context = {
        'session': session,
        'study_group': session.study_group,
        'attendance_records': attendance_records,
        'student_attendance': student_attendance,
        'student': student,
    }
    
    return render(request, 'community/group_session_detail.html', context)


@login_required
@role_required('student')
def update_session_attendance(request, session_id):
    """API endpoint to update student's attendance status for a session"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return JsonResponse({'error': 'Student profile not found'}, status=400)
    
    session = get_object_or_404(StudySession, id=session_id, session_type='group')
    
    # Check if student is a member of the group
    if not session.study_group.is_member(student):
        return JsonResponse({'error': 'Not a member of this group'}, status=403)
    
    try:
        data = json.loads(request.body)
        status = data.get('status')
        
        if status not in ['confirmed', 'cancelled']:
            return JsonResponse({'error': 'Invalid status'}, status=400)
        
        # Update or create attendance record
        attendance, created = StudySessionAttendance.objects.get_or_create(
            session=session,
            student=student,
            defaults={'status': status}
        )
        
        if not created:
            attendance.status = status
            attendance.save()
        
        return JsonResponse({
            'status': attendance.status,
            'message': f'Attendance updated to {status}'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Failed to update attendance'}, status=500)
