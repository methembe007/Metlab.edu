"""
Forms for video chat session management.
"""
from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import VideoSession, VideoSessionParticipant

User = get_user_model()


class VideoSessionScheduleForm(forms.ModelForm):
    """Form for scheduling video sessions"""
    
    # Additional fields for participant selection
    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Select participants to invite to this session"
    )
    
    # Override scheduled_time to use datetime-local input
    scheduled_time = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }
        ),
        help_text="Select date and time for the session (your local timezone)"
    )
    
    class Meta:
        model = VideoSession
        fields = [
            'title',
            'description',
            'session_type',
            'scheduled_time',
            'duration_minutes',
            'max_participants',
            'allow_screen_share',
            'require_approval',
            'teacher_class',
            'tutor_booking'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter session title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional session description'
            }),
            'session_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 15,
                'max': 240,
                'step': 15
            }),
            'max_participants': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 2,
                'max': 30
            }),
            'allow_screen_share': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'require_approval': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'teacher_class': forms.Select(attrs={
                'class': 'form-control'
            }),
            'tutor_booking': forms.Select(attrs={
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set default scheduled time to 1 hour from now
        if not self.instance.pk:
            default_time = timezone.now() + timedelta(hours=1)
            # Format for datetime-local input (YYYY-MM-DDTHH:MM)
            self.initial['scheduled_time'] = default_time.strftime('%Y-%m-%dT%H:%M')
        
        # Filter teacher_class queryset based on user
        if self.user:
            from learning.teacher_models import TeacherClass
            
            # Check if user has teacher profile
            if hasattr(self.user, 'teacher_profile'):
                self.fields['teacher_class'].queryset = TeacherClass.objects.filter(
                    teacher=self.user.teacher_profile
                )
            else:
                self.fields['teacher_class'].queryset = TeacherClass.objects.none()
            
            # Filter tutor_booking queryset based on user
            from community.models import TutorBooking
            from django.db import models as django_models
            
            # Show bookings where user is tutor or student
            tutor_bookings_query = django_models.Q(tutor__user=self.user)
            if hasattr(self.user, 'student_profile'):
                tutor_bookings_query |= django_models.Q(student=self.user.student_profile)
            
            self.fields['tutor_booking'].queryset = TutorBooking.objects.filter(
                tutor_bookings_query
            ).select_related('tutor__user', 'student')
            
            # Set up participants queryset
            # For teachers, show their students
            # For students, show their teachers
            if hasattr(self.user, 'teacher_profile'):
                # Get all students enrolled in teacher's classes
                from learning.teacher_models import ClassEnrollment
                student_user_ids = ClassEnrollment.objects.filter(
                    teacher_class__teacher=self.user.teacher_profile,
                    is_active=True
                ).values_list('student__user_id', flat=True)
                self.fields['participants'].queryset = User.objects.filter(
                    id__in=student_user_ids
                ).order_by('username')
            elif hasattr(self.user, 'student_profile'):
                # Get all teachers of classes the student is enrolled in
                from learning.teacher_models import ClassEnrollment
                teacher_ids = ClassEnrollment.objects.filter(
                    student=self.user.student_profile
                ).values_list('teacher_class__teacher__user_id', flat=True)
                self.fields['participants'].queryset = User.objects.filter(
                    id__in=teacher_ids
                ).order_by('username')
            else:
                self.fields['participants'].queryset = User.objects.none()
        
        # Make teacher_class and tutor_booking optional
        self.fields['teacher_class'].required = False
        self.fields['tutor_booking'].required = False
        
        # Set help texts
        self.fields['duration_minutes'].help_text = "Expected session duration (15-240 minutes)"
        self.fields['max_participants'].help_text = "Maximum number of participants (2-30)"
    
    def clean_scheduled_time(self):
        """Validate scheduled time is in the future"""
        scheduled_time = self.cleaned_data.get('scheduled_time')
        
        if scheduled_time:
            # Allow scheduling up to 10 minutes before (for early join)
            min_time = timezone.now() - timedelta(minutes=10)
            
            if scheduled_time < min_time:
                raise forms.ValidationError(
                    "Scheduled time must be in the future (or within 10 minutes for early join)"
                )
        
        return scheduled_time
    
    def clean(self):
        """Additional validation"""
        cleaned_data = super().clean()
        session_type = cleaned_data.get('session_type')
        max_participants = cleaned_data.get('max_participants')
        teacher_class = cleaned_data.get('teacher_class')
        tutor_booking = cleaned_data.get('tutor_booking')
        
        # Validate one-on-one sessions have max 2 participants
        if session_type == 'one_on_one' and max_participants and max_participants > 2:
            cleaned_data['max_participants'] = 2
        
        # Validate class sessions have a teacher_class
        if session_type == 'class' and not teacher_class:
            raise forms.ValidationError({
                'teacher_class': "Class sessions must be linked to a teacher class"
            })
        
        # Validate one-on-one sessions with tutor_booking
        if tutor_booking and session_type != 'one_on_one':
            raise forms.ValidationError({
                'session_type': "Tutor booking sessions must be one-on-one"
            })
        
        return cleaned_data


class VideoSessionQuickStartForm(forms.Form):
    """Form for quickly starting an immediate video session"""
    
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter session title'
        })
    )
    
    session_type = forms.ChoiceField(
        choices=VideoSession.SESSION_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Select participants to invite"
    )
    
    allow_screen_share = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label="Allow screen sharing"
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set up participants queryset based on user
        if self.user:
            if hasattr(self.user, 'teacher_profile'):
                # Get all students enrolled in teacher's classes
                from learning.teacher_models import ClassEnrollment
                student_user_ids = ClassEnrollment.objects.filter(
                    teacher_class__teacher=self.user.teacher_profile,
                    is_active=True
                ).values_list('student__user_id', flat=True)
                self.fields['participants'].queryset = User.objects.filter(
                    id__in=student_user_ids
                ).order_by('username')
            elif hasattr(self.user, 'student_profile'):
                # Get all teachers of classes the student is enrolled in
                from learning.teacher_models import ClassEnrollment
                teacher_ids = ClassEnrollment.objects.filter(
                    student=self.user.student_profile
                ).values_list('teacher_class__teacher__user_id', flat=True)
                self.fields['participants'].queryset = User.objects.filter(
                    id__in=teacher_ids
                ).order_by('username')
            else:
                self.fields['participants'].queryset = User.objects.none()


class VideoSessionEditForm(forms.ModelForm):
    """Form for editing scheduled video sessions"""
    
    scheduled_time = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }
        ),
        help_text="Select date and time for the session (your local timezone)"
    )
    
    class Meta:
        model = VideoSession
        fields = [
            'title',
            'description',
            'scheduled_time',
            'duration_minutes',
            'max_participants',
            'allow_screen_share'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 15,
                'max': 240,
                'step': 15
            }),
            'max_participants': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 2,
                'max': 30
            }),
            'allow_screen_share': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def clean_scheduled_time(self):
        """Validate scheduled time is in the future"""
        scheduled_time = self.cleaned_data.get('scheduled_time')
        
        if scheduled_time:
            min_time = timezone.now() - timedelta(minutes=10)
            
            if scheduled_time < min_time:
                raise forms.ValidationError(
                    "Scheduled time must be in the future"
                )
        
        return scheduled_time
