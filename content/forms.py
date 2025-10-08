"""
Forms for content upload and management.
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import UploadedContent


class ContentUploadForm(forms.ModelForm):
    """Form for uploading content files"""
    
    subject = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter subject (optional)'
        }),
        help_text="Optional: Specify the subject or topic of this content"
    )
    
    difficulty_level = forms.ChoiceField(
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        initial='intermediate',
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        help_text="Select the difficulty level of this content"
    )
    
    class Meta:
        model = UploadedContent
        fields = ['file', 'subject', 'difficulty_level']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'hidden',
                'id': 'file-upload',
                'accept': '.pdf,.docx,.txt,.jpg,.jpeg,.png,.pptx'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].help_text = (
            "Supported formats: PDF, DOCX, TXT, JPG, PNG, PPTX. "
            "Maximum file size: 50MB"
        )
    
    def clean_file(self):
        """Validate uploaded file"""
        file = self.cleaned_data.get('file')
        
        if not file:
            raise ValidationError("Please select a file to upload.")
        
        # Check file size (50MB limit)
        if file.size > 50 * 1024 * 1024:
            raise ValidationError("File size cannot exceed 50MB.")
        
        # Check file extension
        allowed_extensions = ['.pdf', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.pptx']
        file_extension = file.name.lower().split('.')[-1]
        
        if f'.{file_extension}' not in allowed_extensions:
            raise ValidationError(
                f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        return file
    
    def clean_subject(self):
        """Clean and validate subject field"""
        subject = self.cleaned_data.get('subject', '').strip()
        
        if subject and len(subject) < 2:
            raise ValidationError("Subject must be at least 2 characters long.")
        
        return subject


class ContentSearchForm(forms.Form):
    """Form for searching content in the library"""
    
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Search by filename, subject, or content...'
        })
    )
    
    status = forms.ChoiceField(
        choices=[
            ('', 'All Status'),
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    
    content_type = forms.ChoiceField(
        choices=[
            ('', 'All Types'),
            ('pdf', 'PDF'),
            ('docx', 'Word Document'),
            ('txt', 'Text File'),
            ('image', 'Image'),
            ('pptx', 'PowerPoint'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )