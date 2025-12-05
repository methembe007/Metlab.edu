"""
Permission and access control logic for video chat sessions.
Implements security checks for session access based on user relationships.
Requirements: 1.1, 1.2, 4.1, 4.2
"""
import logging
from django.core.exceptions import PermissionDenied
from .models import VideoSession, VideoSessionParticipant

logger = logging.getLogger(__name__)


class VideoSessionPermissions:
    """
    Centralized permission checking for video chat sessions.
    Verifies user authorization based on session type and relationships.
    """
    
    @staticmethod
    def can_user_join_session(user, session):
        """
        Check if a user is authorized to join a video session.
        
        Args:
            user: User object attempting to join
            session: VideoSession instance
            
        Returns:
            tuple: (can_join: bool, reason: str)
            
        Requirements: 1.2, 4.1, 4.2
        """
        # Host is always authorized
        if session.host == user:
            return True, "User is the session host"
        
        # Check if user is already a participant (invited or joined)
        is_participant = VideoSessionParticipant.objects.filter(
            session=session,
            user=user
        ).exclude(status='removed').exists()
        
        if is_participant:
            return True, "User is an invited participant"
        
        # Check based on session type
        if session.session_type == 'one_on_one':
            return VideoSessionPermissions._check_one_on_one_access(user, session)
        
        elif session.session_type == 'class' and session.teacher_class:
            return VideoSessionPermissions._check_class_session_access(user, session)
        
        elif session.session_type == 'group':
            # For group sessions without specific class, check if approval is required
            if not session.require_approval:
                return True, "Group session does not require approval"
            return False, "Group session requires approval to join"
        
        # Check if linked to tutor booking
        if session.tutor_booking:
            return VideoSessionPermissions._check_tutor_booking_access(user, session)
        
        return False, "User is not authorized to join this session"
    
    @staticmethod
    def _check_one_on_one_access(user, session):
        """
        Check access for one-on-one sessions.
        Verifies teacher-student relationships.
        
        Requirements: 1.1, 1.2
        """
        from accounts.models import StudentProfile, TeacherProfile
        from learning.teacher_models import ClassEnrollment
        
        try:
            # Check if user is a student
            student_profile = StudentProfile.objects.filter(user=user).first()
            if student_profile:
                # Check if host is a teacher with this student in their class
                teacher_profile = TeacherProfile.objects.filter(user=session.host).first()
                if teacher_profile:
                    # Check if student is enrolled in any of the teacher's classes
                    is_enrolled = ClassEnrollment.objects.filter(
                        teacher_class__teacher=teacher_profile,
                        student=student_profile,
                        is_active=True
                    ).exists()
                    
                    if is_enrolled:
                        # Check parent consent for minors
                        consent_granted, consent_reason = VideoSessionPermissions._check_parent_consent(user)
                        if not consent_granted:
                            return False, consent_reason
                        
                        return True, "Student is enrolled in teacher's class"
                
                # Check if host is another student (peer-to-peer study session)
                host_student_profile = StudentProfile.objects.filter(user=session.host).first()
                if host_student_profile:
                    # Check if they are study partners
                    from community.models import StudyPartnership
                    are_partners = StudyPartnership.objects.filter(
                        status='active'
                    ).filter(
                        models.Q(student1=student_profile, student2=host_student_profile) |
                        models.Q(student1=host_student_profile, student2=student_profile)
                    ).exists()
                    
                    if are_partners:
                        # Check parent consent for minors
                        consent_granted, consent_reason = VideoSessionPermissions._check_parent_consent(user)
                        if not consent_granted:
                            return False, consent_reason
                        
                        return True, "Users are study partners"
            
            # Check if user is a teacher
            teacher_profile = TeacherProfile.objects.filter(user=user).first()
            if teacher_profile:
                # Check if host is a student in their class
                host_student_profile = StudentProfile.objects.filter(user=session.host).first()
                if host_student_profile:
                    is_enrolled = ClassEnrollment.objects.filter(
                        teacher_class__teacher=teacher_profile,
                        student=host_student_profile,
                        is_active=True
                    ).exists()
                    
                    if is_enrolled:
                        return True, "Teacher has student in their class"
            
        except Exception as e:
            logger.error(f"Error checking one-on-one access: {str(e)}")
            return False, "Error verifying relationship"
        
        return False, "No valid teacher-student or study partner relationship found"
    
    @staticmethod
    def _check_class_session_access(user, session):
        """
        Check access for class sessions.
        Verifies class enrollment.
        
        Requirements: 2.1, 2.3
        """
        from accounts.models import StudentProfile
        from learning.teacher_models import ClassEnrollment
        
        try:
            # Check if user is enrolled in the class
            student_profile = StudentProfile.objects.filter(user=user).first()
            if student_profile:
                is_enrolled = ClassEnrollment.objects.filter(
                    teacher_class=session.teacher_class,
                    student=student_profile,
                    is_active=True
                ).exists()
                
                if is_enrolled:
                    # Check parent consent for minors
                    consent_granted, consent_reason = VideoSessionPermissions._check_parent_consent(user)
                    if not consent_granted:
                        return False, consent_reason
                    
                    return True, "Student is enrolled in the class"
            
            # Check if user is the teacher of the class
            if session.teacher_class.teacher.user == user:
                return True, "User is the class teacher"
            
        except Exception as e:
            logger.error(f"Error checking class session access: {str(e)}")
            return False, "Error verifying class enrollment"
        
        return False, "User is not enrolled in this class"
    
    @staticmethod
    def _check_tutor_booking_access(user, session):
        """
        Check access for tutoring sessions.
        Validates tutor booking relationships.
        
        Requirements: 1.1, 1.2
        """
        try:
            tutor_booking = session.tutor_booking
            
            # Check if user is the tutor
            if tutor_booking.tutor.user == user:
                return True, "User is the tutor for this booking"
            
            # Check if user is the student
            if tutor_booking.student.user == user:
                # Check parent consent for minors
                consent_granted, consent_reason = VideoSessionPermissions._check_parent_consent(user)
                if not consent_granted:
                    return False, consent_reason
                
                return True, "User is the student for this booking"
            
        except Exception as e:
            logger.error(f"Error checking tutor booking access: {str(e)}")
            return False, "Error verifying tutor booking"
        
        return False, "User is not part of this tutor booking"
    
    @staticmethod
    def _check_parent_consent(user):
        """
        Check if parent consent is required and granted for minors.
        Enforces COPPA compliance for users under 13.
        
        Requirements: 4.2
        """
        from accounts.models import COPPACompliance
        
        try:
            # Check if user has COPPA compliance record
            coppa_record = COPPACompliance.objects.filter(user=user).first()
            
            if coppa_record and coppa_record.is_under_13:
                # User is under 13, check parent consent
                if not coppa_record.parent_consent_given:
                    return False, "Parent consent required for users under 13"
                
                # Verify parent consent is still valid
                if not coppa_record.parent_consent_date:
                    return False, "Parent consent not properly recorded"
            
            # No COPPA record or user is 13+, consent not required
            return True, "Parent consent not required or already granted"
            
        except Exception as e:
            logger.error(f"Error checking parent consent: {str(e)}")
            # Fail safe: deny access if we can't verify consent
            return False, "Error verifying parent consent"
    
    @staticmethod
    def can_user_create_session(user, session_type, teacher_class=None, tutor_booking=None):
        """
        Check if a user can create a video session of a specific type.
        
        Args:
            user: User attempting to create the session
            session_type: Type of session ('one_on_one', 'group', 'class')
            teacher_class: Optional TeacherClass for class sessions
            tutor_booking: Optional TutorBooking for tutoring sessions
            
        Returns:
            tuple: (can_create: bool, reason: str)
        """
        from accounts.models import TeacherProfile, StudentProfile
        from community.models import TutorProfile
        
        # Check for class sessions
        if session_type == 'class':
            if not teacher_class:
                return False, "Class session requires a teacher class"
            
            # Only the class teacher can create class sessions
            teacher_profile = TeacherProfile.objects.filter(user=user).first()
            if not teacher_profile:
                return False, "Only teachers can create class sessions"
            
            if teacher_class.teacher != teacher_profile:
                return False, "Only the class teacher can create sessions for this class"
            
            return True, "Teacher can create class session"
        
        # Check for tutor booking sessions
        if tutor_booking:
            # Only the tutor can create the session
            tutor_profile = TutorProfile.objects.filter(user=user).first()
            if not tutor_profile:
                return False, "Only tutors can create tutor booking sessions"
            
            if tutor_booking.tutor != tutor_profile:
                return False, "Only the assigned tutor can create this session"
            
            return True, "Tutor can create booking session"
        
        # For one-on-one and group sessions, check if user has appropriate profile
        student_profile = StudentProfile.objects.filter(user=user).first()
        teacher_profile = TeacherProfile.objects.filter(user=user).first()
        tutor_profile = TutorProfile.objects.filter(user=user).first()
        
        if not (student_profile or teacher_profile or tutor_profile):
            return False, "User must have a student, teacher, or tutor profile"
        
        return True, "User can create session"
    
    @staticmethod
    def can_user_invite_participant(host_user, participant_user, session):
        """
        Check if a host can invite a specific participant to a session.
        
        Args:
            host_user: User who is the session host
            participant_user: User being invited
            session: VideoSession instance
            
        Returns:
            tuple: (can_invite: bool, reason: str)
        """
        from accounts.models import TeacherProfile, StudentProfile
        from learning.teacher_models import ClassEnrollment
        
        # Verify host is actually the session host
        if session.host != host_user:
            return False, "Only the session host can invite participants"
        
        # For class sessions, can only invite enrolled students
        if session.session_type == 'class' and session.teacher_class:
            student_profile = StudentProfile.objects.filter(user=participant_user).first()
            if not student_profile:
                return False, "Can only invite students to class sessions"
            
            is_enrolled = ClassEnrollment.objects.filter(
                teacher_class=session.teacher_class,
                student=student_profile,
                is_active=True
            ).exists()
            
            if not is_enrolled:
                return False, "Student is not enrolled in this class"
            
            # Check parent consent for minors
            consent_granted, consent_reason = VideoSessionPermissions._check_parent_consent(participant_user)
            if not consent_granted:
                return False, consent_reason
            
            return True, "Can invite enrolled student"
        
        # For one-on-one sessions, verify relationship
        if session.session_type == 'one_on_one':
            # Check teacher-student relationship
            host_teacher = TeacherProfile.objects.filter(user=host_user).first()
            participant_student = StudentProfile.objects.filter(user=participant_user).first()
            
            if host_teacher and participant_student:
                is_enrolled = ClassEnrollment.objects.filter(
                    teacher_class__teacher=host_teacher,
                    student=participant_student,
                    is_active=True
                ).exists()
                
                if is_enrolled:
                    # Check parent consent for minors
                    consent_granted, consent_reason = VideoSessionPermissions._check_parent_consent(participant_user)
                    if not consent_granted:
                        return False, consent_reason
                    
                    return True, "Can invite student from class"
            
            # Check study partner relationship
            host_student = StudentProfile.objects.filter(user=host_user).first()
            if host_student and participant_student:
                from community.models import StudyPartnership
                from django.db import models
                
                are_partners = StudyPartnership.objects.filter(
                    status='active'
                ).filter(
                    models.Q(student1=host_student, student2=participant_student) |
                    models.Q(student1=participant_student, student2=host_student)
                ).exists()
                
                if are_partners:
                    # Check parent consent for minors
                    consent_granted, consent_reason = VideoSessionPermissions._check_parent_consent(participant_user)
                    if not consent_granted:
                        return False, consent_reason
                    
                    return True, "Can invite study partner"
        
        # For group sessions, more flexible invitation rules
        if session.session_type == 'group':
            # Check parent consent for minors
            consent_granted, consent_reason = VideoSessionPermissions._check_parent_consent(participant_user)
            if not consent_granted:
                return False, consent_reason
            
            return True, "Can invite to group session"
        
        return False, "No valid relationship for invitation"
    
    @staticmethod
    def can_user_remove_participant(host_user, participant_user, session):
        """
        Check if a host can remove a specific participant from a session.
        
        Args:
            host_user: User who is the session host
            participant_user: User being removed
            session: VideoSession instance
            
        Returns:
            tuple: (can_remove: bool, reason: str)
        """
        # Only the host can remove participants
        if session.host != host_user:
            return False, "Only the session host can remove participants"
        
        # Cannot remove the host themselves
        if participant_user == host_user:
            return False, "Cannot remove the session host"
        
        # Check if participant is in the session
        is_participant = VideoSessionParticipant.objects.filter(
            session=session,
            user=participant_user
        ).exists()
        
        if not is_participant:
            return False, "User is not a participant in this session"
        
        return True, "Host can remove participant"
    
    @staticmethod
    def enforce_session_access(user, session):
        """
        Enforce session access control, raising PermissionDenied if unauthorized.
        
        Args:
            user: User attempting to access the session
            session: VideoSession instance
            
        Raises:
            PermissionDenied: If user is not authorized
        """
        can_join, reason = VideoSessionPermissions.can_user_join_session(user, session)
        
        if not can_join:
            logger.warning(
                f"Access denied for user {user.username} to session {session.session_id}: {reason}"
            )
            raise PermissionDenied(reason)
        
        logger.info(
            f"Access granted for user {user.username} to session {session.session_id}: {reason}"
        )
