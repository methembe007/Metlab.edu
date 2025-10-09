from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from accounts.models import StudentProfile
from decimal import Decimal

User = get_user_model()


class Subject(models.Model):
    """Model for academic subjects"""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Name of the academic subject"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of the subject"
    )
    category = models.CharField(
        max_length=50,
        blank=True,
        help_text="Subject category (e.g., STEM, Humanities, Languages)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class TutorProfile(models.Model):
    """Profile model for tutors with expertise and availability"""
    
    EXPERIENCE_LEVEL_CHOICES = [
        ('beginner', 'Beginner (0-2 years)'),
        ('intermediate', 'Intermediate (3-5 years)'),
        ('experienced', 'Experienced (6-10 years)'),
        ('expert', 'Expert (10+ years)'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending Approval'),
        ('suspended', 'Suspended'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='tutor_profile'
    )
    subjects = models.ManyToManyField(
        Subject,
        related_name='tutors',
        help_text="Subjects the tutor can teach"
    )
    bio = models.TextField(
        help_text="Tutor's professional biography and teaching approach"
    )
    experience_level = models.CharField(
        max_length=15,
        choices=EXPERIENCE_LEVEL_CHOICES,
        help_text="Tutor's experience level"
    )
    hourly_rate = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('5.00'))],
        help_text="Hourly rate in USD"
    )
    rating = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="Average rating from student reviews"
    )
    total_reviews = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total number of reviews received"
    )
    total_sessions = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total number of tutoring sessions completed"
    )
    languages = models.JSONField(
        default=list,
        help_text="Languages the tutor can teach in"
    )
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text="Tutor's timezone for scheduling"
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the tutor profile"
    )
    verified = models.BooleanField(
        default=False,
        help_text="Whether the tutor's credentials have been verified"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def update_rating(self):
        """Update the tutor's average rating based on reviews"""
        reviews = self.reviews.all()
        if reviews.exists():
            total_rating = sum(review.rating for review in reviews)
            self.rating = total_rating / reviews.count()
            self.total_reviews = reviews.count()
            self.save(update_fields=['rating', 'total_reviews'])
    
    def is_available_at(self, datetime_obj):
        """Check if tutor is available at a specific datetime"""
        # Check if there's an availability slot for this time
        weekday = datetime_obj.weekday()  # 0=Monday, 6=Sunday
        time_obj = datetime_obj.time()
        
        availability = self.availability_slots.filter(
            day_of_week=weekday,
            start_time__lte=time_obj,
            end_time__gt=time_obj,
            is_available=True
        ).exists()
        
        # Check if there's no conflicting booking
        no_booking = not self.bookings.filter(
            scheduled_time__date=datetime_obj.date(),
            scheduled_time__time=time_obj,
            status__in=['confirmed', 'in_progress']
        ).exists()
        
        return availability and no_booking
    
    def get_compatibility_score(self, student):
        """Calculate compatibility score with a student (0-100)"""
        score = 0
        
        # Subject match (40 points max)
        student_subjects = set(student.subjects_of_interest)
        tutor_subjects = set(subject.name for subject in self.subjects.all())
        subject_overlap = len(student_subjects.intersection(tutor_subjects))
        if student_subjects:
            score += (subject_overlap / len(student_subjects)) * 40
        
        # Experience level match (20 points max)
        student_level = student.level
        if student_level <= 3 and self.experience_level in ['beginner', 'intermediate']:
            score += 20
        elif student_level <= 6 and self.experience_level in ['intermediate', 'experienced']:
            score += 20
        elif student_level > 6 and self.experience_level in ['experienced', 'expert']:
            score += 20
        
        # Rating bonus (20 points max)
        score += (self.rating / 5.0) * 20
        
        # Activity bonus (10 points max)
        if self.total_sessions > 10:
            score += 10
        elif self.total_sessions > 5:
            score += 5
        
        # Availability bonus (10 points max)
        if self.availability_slots.filter(is_available=True).count() >= 10:
            score += 10
        elif self.availability_slots.filter(is_available=True).count() >= 5:
            score += 5
        
        return min(100, score)
    
    def __str__(self):
        return f"Tutor: {self.user.get_full_name() or self.user.username}"
    
    class Meta:
        ordering = ['-rating', '-total_sessions']


class TutorAvailability(models.Model):
    """Model for tutor availability slots"""
    
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    tutor = models.ForeignKey(
        TutorProfile,
        on_delete=models.CASCADE,
        related_name='availability_slots'
    )
    day_of_week = models.IntegerField(
        choices=DAY_CHOICES,
        help_text="Day of the week (0=Monday, 6=Sunday)"
    )
    start_time = models.TimeField(
        help_text="Start time of availability slot"
    )
    end_time = models.TimeField(
        help_text="End time of availability slot"
    )
    is_available = models.BooleanField(
        default=True,
        help_text="Whether this slot is currently available"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.tutor.user.username} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"
    
    class Meta:
        unique_together = ['tutor', 'day_of_week', 'start_time', 'end_time']
        ordering = ['day_of_week', 'start_time']


class TutorBooking(models.Model):
    """Model for tutor booking sessions"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Confirmation'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    tutor = models.ForeignKey(
        TutorProfile,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='tutor_bookings'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        help_text="Subject for the tutoring session"
    )
    scheduled_time = models.DateTimeField(
        help_text="Scheduled date and time for the session"
    )
    duration_minutes = models.IntegerField(
        default=60,
        validators=[MinValueValidator(15), MaxValueValidator(180)],
        help_text="Duration of the session in minutes"
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the booking"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes or requirements for the session"
    )
    session_notes = models.TextField(
        blank=True,
        help_text="Notes from the completed session"
    )
    total_cost = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Total cost for the session"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Calculate total cost based on duration and hourly rate
        if not self.total_cost:
            hours = self.duration_minutes / 60
            self.total_cost = self.tutor.hourly_rate * Decimal(str(hours))
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Booking: {self.student.user.username} with {self.tutor.user.username} - {self.scheduled_time}"
    
    class Meta:
        ordering = ['-scheduled_time']


class TutorReview(models.Model):
    """Model for student reviews of tutors"""
    
    tutor = models.ForeignKey(
        TutorProfile,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='tutor_reviews'
    )
    booking = models.OneToOneField(
        TutorBooking,
        on_delete=models.CASCADE,
        related_name='review',
        help_text="The booking this review is for"
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    comment = models.TextField(
        help_text="Written review comment"
    )
    would_recommend = models.BooleanField(
        default=True,
        help_text="Whether the student would recommend this tutor"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update tutor's rating after saving review
        self.tutor.update_rating()
    
    def __str__(self):
        return f"Review: {self.student.user.username} -> {self.tutor.user.username} ({self.rating}/5)"
    
    class Meta:
        unique_together = ['tutor', 'student', 'booking']
        ordering = ['-created_at']


class StudyPartnerRequest(models.Model):
    """Model for study partner requests between students"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('cancelled', 'Cancelled'),
    ]
    
    requester = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='sent_partner_requests',
        help_text="Student who sent the partner request"
    )
    requested = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='received_partner_requests',
        help_text="Student who received the partner request"
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        help_text="Subject for study partnership"
    )
    message = models.TextField(
        blank=True,
        help_text="Optional message from requester"
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the request"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Partner Request: {self.requester.user.username} -> {self.requested.user.username} ({self.subject.name})"
    
    class Meta:
        unique_together = ['requester', 'requested', 'subject']
        ordering = ['-created_at']


class StudyPartnership(models.Model):
    """Model for active study partnerships between students"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('ended', 'Ended'),
    ]
    
    student1 = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='partnerships_as_student1',
        help_text="First student in the partnership"
    )
    student2 = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='partnerships_as_student2',
        help_text="Second student in the partnership"
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        help_text="Subject for study partnership"
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='active',
        help_text="Current status of the partnership"
    )
    total_sessions = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total number of study sessions completed together"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_partner(self, student):
        """Get the partner of the given student"""
        if self.student1 == student:
            return self.student2
        elif self.student2 == student:
            return self.student1
        return None
    
    def __str__(self):
        return f"Partnership: {self.student1.user.username} & {self.student2.user.username} ({self.subject.name})"
    
    class Meta:
        unique_together = ['student1', 'student2', 'subject']
        ordering = ['-created_at']


class StudyGroup(models.Model):
    """Model for study groups where multiple students can collaborate"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('archived', 'Archived'),
    ]
    
    name = models.CharField(
        max_length=100,
        help_text="Name of the study group"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of the study group's purpose and goals"
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='study_groups',
        help_text="Primary subject focus of the study group"
    )
    members = models.ManyToManyField(
        StudentProfile,
        through='StudyGroupMembership',
        related_name='study_groups',
        help_text="Students who are members of this study group"
    )
    created_by = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='created_study_groups',
        help_text="Student who created this study group"
    )
    max_members = models.IntegerField(
        default=6,
        validators=[MinValueValidator(2), MaxValueValidator(12)],
        help_text="Maximum number of members allowed in the group"
    )
    is_public = models.BooleanField(
        default=True,
        help_text="Whether the group is publicly visible and joinable"
    )
    requires_approval = models.BooleanField(
        default=False,
        help_text="Whether new members need approval to join"
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='active',
        help_text="Current status of the study group"
    )
    total_sessions = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total number of study sessions held by this group"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_member_count(self):
        """Get the current number of members in the group"""
        return self.memberships.filter(status='active').count()
    
    def can_join(self):
        """Check if the group can accept new members"""
        return (self.status == 'active' and 
                self.get_member_count() < self.max_members)
    
    def is_member(self, student):
        """Check if a student is an active member of the group"""
        return self.memberships.filter(
            student=student, 
            status='active'
        ).exists()
    
    def __str__(self):
        return f"Study Group: {self.name} ({self.subject.name})"
    
    class Meta:
        ordering = ['-created_at']


class StudyGroupMembership(models.Model):
    """Model for study group membership with roles and status"""
    
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
        ('member', 'Member'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('pending', 'Pending Approval'),
        ('left', 'Left Group'),
        ('removed', 'Removed'),
    ]
    
    study_group = models.ForeignKey(
        StudyGroup,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='group_memberships'
    )
    role = models.CharField(
        max_length=15,
        choices=ROLE_CHOICES,
        default='member',
        help_text="Role of the student in the group"
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='active',
        help_text="Current membership status"
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student.user.username} in {self.study_group.name} ({self.role})"
    
    class Meta:
        unique_together = ['study_group', 'student']
        ordering = ['-joined_at']


class StudyGroupMessage(models.Model):
    """Model for chat messages within study groups"""
    
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Text Message'),
        ('file', 'File Share'),
        ('system', 'System Message'),
    ]
    
    study_group = models.ForeignKey(
        StudyGroup,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='group_messages',
        null=True,
        blank=True,
        help_text="Student who sent the message (null for system messages)"
    )
    message_type = models.CharField(
        max_length=10,
        choices=MESSAGE_TYPE_CHOICES,
        default='text'
    )
    content = models.TextField(
        help_text="Message content or system message text"
    )
    file_attachment = models.FileField(
        upload_to='study_groups/files/',
        null=True,
        blank=True,
        help_text="Optional file attachment"
    )
    is_edited = models.BooleanField(
        default=False,
        help_text="Whether the message has been edited"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        sender_name = self.sender.user.username if self.sender else "System"
        return f"Message from {sender_name} in {self.study_group.name}"
    
    class Meta:
        ordering = ['created_at']


class StudySession(models.Model):
    """Model for scheduled study sessions between partners or groups"""
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    SESSION_TYPE_CHOICES = [
        ('partnership', 'Partnership Session'),
        ('group', 'Group Session'),
    ]
    
    # Either partnership or study_group should be set, not both
    partnership = models.ForeignKey(
        StudyPartnership,
        on_delete=models.CASCADE,
        related_name='study_sessions',
        null=True,
        blank=True,
        help_text="The partnership this session belongs to (for partner sessions)"
    )
    study_group = models.ForeignKey(
        StudyGroup,
        on_delete=models.CASCADE,
        related_name='study_sessions',
        null=True,
        blank=True,
        help_text="The study group this session belongs to (for group sessions)"
    )
    session_type = models.CharField(
        max_length=15,
        choices=SESSION_TYPE_CHOICES,
        help_text="Type of study session"
    )
    title = models.CharField(
        max_length=200,
        help_text="Title or name of the study session"
    )
    scheduled_time = models.DateTimeField(
        help_text="Scheduled date and time for the study session"
    )
    duration_minutes = models.IntegerField(
        default=60,
        validators=[MinValueValidator(15), MaxValueValidator(240)],
        help_text="Duration of the session in minutes"
    )
    topic = models.CharField(
        max_length=200,
        blank=True,
        help_text="Specific topic or focus for the session"
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='scheduled',
        help_text="Current status of the session"
    )
    description = models.TextField(
        blank=True,
        help_text="Description, notes, or agenda for the session"
    )
    session_summary = models.TextField(
        blank=True,
        help_text="Summary of what was covered in the session"
    )
    room_id = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        help_text="Unique identifier for the study room"
    )
    attendees = models.ManyToManyField(
        StudentProfile,
        through='StudySessionAttendance',
        related_name='attended_sessions',
        help_text="Students who attended this session"
    )
    created_by = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='created_study_sessions',
        help_text="Student who created this session"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Generate room_id if not provided
        if not self.room_id:
            import uuid
            self.room_id = str(uuid.uuid4())
        
        # Set session_type based on which relationship is set
        if self.partnership and not self.study_group:
            self.session_type = 'partnership'
        elif self.study_group and not self.partnership:
            self.session_type = 'group'
        
        super().save(*args, **kwargs)
    
    def get_participants(self):
        """Get all participants for this session"""
        if self.session_type == 'partnership' and self.partnership:
            return [self.partnership.student1, self.partnership.student2]
        elif self.session_type == 'group' and self.study_group:
            return list(self.study_group.members.filter(
                group_memberships__status='active'
            ))
        return []
    
    def __str__(self):
        if self.session_type == 'partnership':
            return f"Study Session: {self.partnership} - {self.scheduled_time}"
        else:
            return f"Group Session: {self.study_group.name} - {self.scheduled_time}"
    
    class Meta:
        ordering = ['-scheduled_time']


class StudySessionAttendance(models.Model):
    """Model to track attendance for study sessions"""
    
    STATUS_CHOICES = [
        ('invited', 'Invited'),
        ('confirmed', 'Confirmed'),
        ('attended', 'Attended'),
        ('missed', 'Missed'),
        ('cancelled', 'Cancelled'),
    ]
    
    session = models.ForeignKey(
        StudySession,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='session_attendance'
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='invited'
    )
    joined_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the student joined the session"
    )
    left_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the student left the session"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_duration_minutes(self):
        """Calculate how long the student was in the session"""
        if self.joined_at and self.left_at:
            duration = self.left_at - self.joined_at
            return int(duration.total_seconds() / 60)
        return 0
    
    def __str__(self):
        return f"{self.student.user.username} - {self.session.title} ({self.status})"
    
    class Meta:
        unique_together = ['session', 'student']
        ordering = ['-created_at']


class StudyRoomReport(models.Model):
    """Model for reporting issues in study rooms"""
    
    ISSUE_TYPE_CHOICES = [
        ('inappropriate_behavior', 'Inappropriate Behavior'),
        ('harassment', 'Harassment'),
        ('spam', 'Spam'),
        ('technical_issue', 'Technical Issue'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    session = models.ForeignKey(
        StudySession,
        on_delete=models.CASCADE,
        related_name='reports'
    )
    reporter = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='study_room_reports'
    )
    issue_type = models.CharField(
        max_length=25,
        choices=ISSUE_TYPE_CHOICES,
        help_text="Type of issue being reported"
    )
    description = models.TextField(
        help_text="Detailed description of the issue"
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='pending'
    )
    moderator_notes = models.TextField(
        blank=True,
        help_text="Notes from moderator review"
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the issue was resolved"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Report: {self.get_issue_type_display()} in {self.session.title}"
    
    class Meta:
        ordering = ['-created_at']
