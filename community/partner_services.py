"""
Study partner matching and recommendation services
"""

from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta
from accounts.models import StudentProfile
from learning.models import LearningSession, WeaknessAnalysis
from .models import StudyPartnership, StudyPartnerRequest, Subject
import random


class StudyPartnerMatcher:
    """Service for matching students with compatible study partners"""
    
    def __init__(self):
        self.compatibility_weights = {
            'subject_overlap': 0.3,
            'performance_similarity': 0.25,
            'activity_level': 0.2,
            'learning_preferences': 0.15,
            'availability': 0.1
        }
    
    def get_partner_recommendations(self, student, subject=None, limit=10):
        """
        Get study partner recommendations for a student
        
        Args:
            student: StudentProfile instance
            subject: Optional Subject instance to filter by
            limit: Maximum number of recommendations to return
            
        Returns:
            List of tuples (StudentProfile, compatibility_score)
        """
        # Get potential partners (exclude self and existing partners)
        existing_partners = self._get_existing_partners(student)
        pending_requests = self._get_pending_requests(student)
        
        potential_partners = StudentProfile.objects.exclude(
            Q(id=student.id) |
            Q(id__in=existing_partners) |
            Q(id__in=pending_requests)
        ).select_related('user')
        
        # Filter by subject if specified
        if subject:
            potential_partners = potential_partners.filter(
                subjects_of_interest__contains=[subject.name]
            )
        
        # Calculate compatibility scores
        recommendations = []
        for partner in potential_partners:
            score = self.calculate_compatibility_score(student, partner, subject)
            if score > 30:  # Minimum compatibility threshold
                recommendations.append((partner, score))
        
        # Sort by compatibility score and return top recommendations
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations[:limit]
    
    def calculate_compatibility_score(self, student1, student2, subject=None):
        """
        Calculate compatibility score between two students (0-100)
        
        Args:
            student1: First StudentProfile
            student2: Second StudentProfile
            subject: Optional Subject to focus compatibility on
            
        Returns:
            Float compatibility score (0-100)
        """
        score = 0.0
        
        # Subject overlap score
        subject_score = self._calculate_subject_compatibility(student1, student2, subject)
        score += subject_score * self.compatibility_weights['subject_overlap']
        
        # Performance similarity score
        performance_score = self._calculate_performance_compatibility(student1, student2, subject)
        score += performance_score * self.compatibility_weights['performance_similarity']
        
        # Activity level compatibility
        activity_score = self._calculate_activity_compatibility(student1, student2)
        score += activity_score * self.compatibility_weights['activity_level']
        
        # Learning preferences compatibility
        preferences_score = self._calculate_preferences_compatibility(student1, student2)
        score += preferences_score * self.compatibility_weights['learning_preferences']
        
        # Availability compatibility (simplified)
        availability_score = self._calculate_availability_compatibility(student1, student2)
        score += availability_score * self.compatibility_weights['availability']
        
        return min(100.0, score * 100)
    
    def _calculate_subject_compatibility(self, student1, student2, subject=None):
        """Calculate subject overlap compatibility (0-1)"""
        subjects1 = set(student1.subjects_of_interest)
        subjects2 = set(student2.subjects_of_interest)
        
        if not subjects1 or not subjects2:
            return 0.0
        
        if subject:
            # If specific subject, check if both students are interested
            if subject.name in subjects1 and subject.name in subjects2:
                return 1.0
            else:
                return 0.0
        
        # Calculate overall subject overlap
        overlap = len(subjects1.intersection(subjects2))
        total_unique = len(subjects1.union(subjects2))
        
        if total_unique == 0:
            return 0.0
        
        return overlap / total_unique
    
    def _calculate_performance_compatibility(self, student1, student2, subject=None):
        """Calculate performance level compatibility (0-1)"""
        # Use student levels as a proxy for performance
        level1 = student1.level
        level2 = student2.level
        
        # Students with similar levels are more compatible
        level_diff = abs(level1 - level2)
        
        if level_diff == 0:
            return 1.0
        elif level_diff <= 2:
            return 0.8
        elif level_diff <= 4:
            return 0.6
        elif level_diff <= 6:
            return 0.4
        else:
            return 0.2
    
    def _calculate_activity_compatibility(self, student1, student2):
        """Calculate activity level compatibility (0-1)"""
        # Compare learning streaks and recent activity
        streak1 = student1.current_streak
        streak2 = student2.current_streak
        
        # Get recent learning sessions (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        sessions1 = LearningSession.objects.filter(
            student=student1,
            start_time__gte=thirty_days_ago
        ).count()
        
        sessions2 = LearningSession.objects.filter(
            student=student2,
            start_time__gte=thirty_days_ago
        ).count()
        
        # Normalize activity levels
        max_sessions = max(sessions1, sessions2, 1)
        activity_similarity = 1 - abs(sessions1 - sessions2) / max_sessions
        
        # Normalize streak similarity
        max_streak = max(streak1, streak2, 1)
        streak_similarity = 1 - abs(streak1 - streak2) / max_streak
        
        return (activity_similarity + streak_similarity) / 2
    
    def _calculate_preferences_compatibility(self, student1, student2):
        """Calculate learning preferences compatibility (0-1)"""
        prefs1 = student1.learning_preferences
        prefs2 = student2.learning_preferences
        
        if not prefs1 or not prefs2:
            return 0.5  # Neutral score if no preferences set
        
        # Compare specific preference fields
        compatibility_factors = []
        
        # Study time preferences
        if 'preferred_study_time' in prefs1 and 'preferred_study_time' in prefs2:
            time1 = prefs1['preferred_study_time']
            time2 = prefs2['preferred_study_time']
            if time1 == time2:
                compatibility_factors.append(1.0)
            else:
                compatibility_factors.append(0.3)
        
        # Learning style preferences
        if 'learning_style' in prefs1 and 'learning_style' in prefs2:
            style1 = prefs1['learning_style']
            style2 = prefs2['learning_style']
            if style1 == style2:
                compatibility_factors.append(1.0)
            else:
                compatibility_factors.append(0.5)
        
        # Difficulty preferences
        if 'preferred_difficulty' in prefs1 and 'preferred_difficulty' in prefs2:
            diff1 = prefs1['preferred_difficulty']
            diff2 = prefs2['preferred_difficulty']
            if diff1 == diff2:
                compatibility_factors.append(1.0)
            else:
                compatibility_factors.append(0.6)
        
        if compatibility_factors:
            return sum(compatibility_factors) / len(compatibility_factors)
        
        return 0.5  # Default neutral score
    
    def _calculate_availability_compatibility(self, student1, student2):
        """Calculate availability compatibility (0-1)"""
        # This is a simplified implementation
        # In a real system, you'd compare actual availability schedules
        
        # For now, assume students in similar timezones are more compatible
        # and students with similar activity patterns have better availability overlap
        
        # Use recent activity patterns as a proxy for availability
        recent_sessions1 = LearningSession.objects.filter(
            student=student1,
            start_time__gte=timezone.now() - timedelta(days=7)
        ).values_list('start_time__hour', flat=True)
        
        recent_sessions2 = LearningSession.objects.filter(
            student=student2,
            start_time__gte=timezone.now() - timedelta(days=7)
        ).values_list('start_time__hour', flat=True)
        
        if not recent_sessions1 or not recent_sessions2:
            return 0.5  # Neutral if no recent activity
        
        # Calculate overlap in active hours
        hours1 = set(recent_sessions1)
        hours2 = set(recent_sessions2)
        
        if not hours1 or not hours2:
            return 0.5
        
        overlap = len(hours1.intersection(hours2))
        total_unique = len(hours1.union(hours2))
        
        return overlap / total_unique if total_unique > 0 else 0.5
    
    def _get_existing_partners(self, student):
        """Get IDs of students who are already study partners"""
        partnerships = StudyPartnership.objects.filter(
            Q(student1=student) | Q(student2=student),
            status='active'
        )
        
        partner_ids = []
        for partnership in partnerships:
            if partnership.student1 == student:
                partner_ids.append(partnership.student2.id)
            else:
                partner_ids.append(partnership.student1.id)
        
        return partner_ids
    
    def _get_pending_requests(self, student):
        """Get IDs of students with pending partner requests"""
        pending_sent = StudyPartnerRequest.objects.filter(
            requester=student,
            status='pending'
        ).values_list('requested_id', flat=True)
        
        pending_received = StudyPartnerRequest.objects.filter(
            requested=student,
            status='pending'
        ).values_list('requester_id', flat=True)
        
        return list(pending_sent) + list(pending_received)


class StudyPartnerService:
    """Service for managing study partner requests and partnerships"""
    
    def __init__(self):
        self.matcher = StudyPartnerMatcher()
    
    def send_partner_request(self, requester, requested, subject, message=""):
        """
        Send a study partner request
        
        Args:
            requester: StudentProfile who is sending the request
            requested: StudentProfile who will receive the request
            subject: Subject for the partnership
            message: Optional message from requester
            
        Returns:
            StudyPartnerRequest instance or None if request already exists
        """
        # Check if request already exists
        existing_request = StudyPartnerRequest.objects.filter(
            Q(requester=requester, requested=requested, subject=subject) |
            Q(requester=requested, requested=requester, subject=subject)
        ).first()
        
        if existing_request:
            return None
        
        # Check if partnership already exists
        existing_partnership = StudyPartnership.objects.filter(
            Q(student1=requester, student2=requested, subject=subject) |
            Q(student1=requested, student2=requester, subject=subject),
            status='active'
        ).first()
        
        if existing_partnership:
            return None
        
        # Create the request
        request = StudyPartnerRequest.objects.create(
            requester=requester,
            requested=requested,
            subject=subject,
            message=message
        )
        
        return request
    
    def accept_partner_request(self, request):
        """
        Accept a study partner request and create partnership
        
        Args:
            request: StudyPartnerRequest instance
            
        Returns:
            StudyPartnership instance
        """
        if request.status != 'pending':
            raise ValueError("Request is not pending")
        
        # Update request status
        request.status = 'accepted'
        request.save()
        
        # Create partnership
        partnership = StudyPartnership.objects.create(
            student1=request.requester,
            student2=request.requested,
            subject=request.subject
        )
        
        return partnership
    
    def decline_partner_request(self, request):
        """
        Decline a study partner request
        
        Args:
            request: StudyPartnerRequest instance
        """
        if request.status != 'pending':
            raise ValueError("Request is not pending")
        
        request.status = 'declined'
        request.save()
    
    def cancel_partner_request(self, request):
        """
        Cancel a study partner request (by requester)
        
        Args:
            request: StudyPartnerRequest instance
        """
        if request.status != 'pending':
            raise ValueError("Request is not pending")
        
        request.status = 'cancelled'
        request.save()
    
    def schedule_study_session(self, partnership, scheduled_time, duration_minutes, 
                             topic="", notes="", created_by=None):
        """
        Schedule a study session between partners
        
        Args:
            partnership: StudyPartnership instance
            scheduled_time: datetime for the session
            duration_minutes: Duration in minutes
            topic: Optional topic for the session
            notes: Optional notes/agenda
            created_by: StudentProfile who created the session
            
        Returns:
            StudySession instance
        """
        from .models import StudySession
        
        if not created_by:
            created_by = partnership.student1
        
        session = StudySession.objects.create(
            partnership=partnership,
            scheduled_time=scheduled_time,
            duration_minutes=duration_minutes,
            topic=topic,
            notes=notes,
            created_by=created_by
        )
        
        return session
    
    def get_student_partnerships(self, student, status='active'):
        """
        Get all partnerships for a student
        
        Args:
            student: StudentProfile instance
            status: Partnership status filter
            
        Returns:
            QuerySet of StudyPartnership instances
        """
        return StudyPartnership.objects.filter(
            Q(student1=student) | Q(student2=student),
            status=status
        ).select_related('student1__user', 'student2__user', 'subject')
    
    def get_student_requests(self, student, request_type='received'):
        """
        Get partner requests for a student
        
        Args:
            student: StudentProfile instance
            request_type: 'received', 'sent', or 'all'
            
        Returns:
            QuerySet of StudyPartnerRequest instances
        """
        if request_type == 'received':
            return StudyPartnerRequest.objects.filter(
                requested=student,
                status='pending'
            ).select_related('requester__user', 'subject')
        elif request_type == 'sent':
            return StudyPartnerRequest.objects.filter(
                requester=student,
                status='pending'
            ).select_related('requested__user', 'subject')
        else:  # all
            return StudyPartnerRequest.objects.filter(
                Q(requester=student) | Q(requested=student)
            ).select_related('requester__user', 'requested__user', 'subject')