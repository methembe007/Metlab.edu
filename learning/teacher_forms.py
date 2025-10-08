from django import forms
from django.core.exceptions import ValidationError
from .teacher_models import TeacherClass, TeacherContent, TeacherQuiz
from content.models import UploadedContent
from accounts.models import StudentProfile
import json


class TeacherClassForm(forms.ModelForm):
    """Form for creating and editing teacher classes"""
    
    class Meta:
        model = TeacherClass
        fields = ['name', 'subject', 'grade_level', 'description', 'max_students']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Enter class name'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'e.g., Mathematics, Science, History'
            }),
            'grade_level': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'e.g., Grade 9, High School, College'
            }),
            'description': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Describe what this class covers...'
            }),
            'max_students': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'min': 1,
                'max': 100
            })
        }


class TeacherContentForm(forms.ModelForm):
    """Form for uploading and managing teacher content"""
    
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100',
            'accept': '.pdf,.docx,.txt,.jpg,.jpeg,.png,.pptx'
        })
    )
    
    assigned_classes = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
        }),
        required=False,
        help_text="Select which classes should have access to this content"
    )
    
    class Meta:
        model = TeacherContent
        fields = ['title', 'description', 'subject', 'grade_level', 'is_public', 'assigned_classes']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Enter content title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Describe the content and learning objectives...'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'e.g., Mathematics, Science, History'
            }),
            'grade_level': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'e.g., Grade 9, High School, College'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
            })
        }
    
    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['assigned_classes'].queryset = teacher.classes.filter(is_active=True)


class TeacherQuizForm(forms.ModelForm):
    """Form for customizing AI-generated quizzes"""
    
    questions_json = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    class Meta:
        model = TeacherQuiz
        fields = ['title', 'instructions', 'time_limit_minutes', 'attempts_allowed', 'due_date', 'assigned_classes']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Enter quiz title'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Enter special instructions for students...'
            }),
            'time_limit_minutes': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'min': 5,
                'max': 180,
                'placeholder': 'Time limit in minutes (optional)'
            }),
            'attempts_allowed': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'min': 1,
                'max': 5,
                'value': 1
            }),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'type': 'datetime-local'
            }),
            'assigned_classes': forms.CheckboxSelectMultiple(attrs={
                'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
            })
        }
    
    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['assigned_classes'].queryset = teacher.classes.filter(is_active=True)
    
    def clean_questions_json(self):
        """Validate and parse the questions JSON"""
        questions_json = self.cleaned_data.get('questions_json')
        if questions_json:
            try:
                questions = json.loads(questions_json)
                if not isinstance(questions, list) or len(questions) == 0:
                    raise ValidationError("Questions must be a non-empty list")
                return questions
            except json.JSONDecodeError:
                raise ValidationError("Invalid JSON format for questions")
        return []


class ClassEnrollmentForm(forms.Form):
    """Form for enrolling students in a class using invitation code"""
    
    invitation_code = forms.CharField(
        max_length=8,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'placeholder': 'Enter 8-character invitation code',
            'style': 'text-transform: uppercase;'
        }),
        help_text="Enter the invitation code provided by your teacher"
    )
    
    def clean_invitation_code(self):
        """Validate the invitation code"""
        code = self.cleaned_data.get('invitation_code', '').upper()
        try:
            teacher_class = TeacherClass.objects.get(invitation_code=code, is_active=True)
            if not teacher_class.can_enroll_students():
                raise ValidationError("This class is full and cannot accept more students.")
            return code
        except TeacherClass.DoesNotExist:
            raise ValidationError("Invalid invitation code. Please check with your teacher.")


class BulkContentDistributionForm(forms.Form):
    """Form for distributing content to multiple classes"""
    
    content_items = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
        }),
        help_text="Select content items to distribute"
    )
    
    target_classes = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
        }),
        help_text="Select classes to distribute content to"
    )
    
    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['content_items'].queryset = teacher.teacher_content.all()
            self.fields['target_classes'].queryset = teacher.classes.filter(is_active=True)


class QuizCustomizationForm(forms.Form):
    """Form for customizing individual quiz questions"""
    
    def __init__(self, *args, **kwargs):
        questions = kwargs.pop('questions', [])
        super().__init__(*args, **kwargs)
        
        for i, question in enumerate(questions):
            # Question text field
            self.fields[f'question_{i}_text'] = forms.CharField(
                initial=question.get('question', ''),
                widget=forms.Textarea(attrs={
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                    'rows': 2
                }),
                label=f"Question {i+1}"
            )
            
            # Question type field
            self.fields[f'question_{i}_type'] = forms.ChoiceField(
                choices=[
                    ('multiple_choice', 'Multiple Choice'),
                    ('true_false', 'True/False'),
                    ('short_answer', 'Short Answer')
                ],
                initial=question.get('type', 'multiple_choice'),
                widget=forms.Select(attrs={
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                })
            )
            
            # Options for multiple choice questions
            if question.get('type') == 'multiple_choice':
                options = question.get('options', [])
                for j, option in enumerate(options):
                    self.fields[f'question_{i}_option_{j}'] = forms.CharField(
                        initial=option,
                        widget=forms.TextInput(attrs={
                            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                        }),
                        label=f"Option {j+1}",
                        required=False
                    )
            
            # Correct answer field
            self.fields[f'question_{i}_answer'] = forms.CharField(
                initial=question.get('correct_answer', ''),
                widget=forms.TextInput(attrs={
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                }),
                label="Correct Answer"
            )
            
            # Explanation field
            self.fields[f'question_{i}_explanation'] = forms.CharField(
                initial=question.get('explanation', ''),
                widget=forms.Textarea(attrs={
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                    'rows': 2
                }),
                label="Explanation (optional)",
                required=False
            )
    
    def get_customized_questions(self):
        """Extract customized questions from form data"""
        questions = []
        i = 0
        while f'question_{i}_text' in self.cleaned_data:
            question = {
                'question': self.cleaned_data[f'question_{i}_text'],
                'type': self.cleaned_data[f'question_{i}_type'],
                'correct_answer': self.cleaned_data[f'question_{i}_answer'],
                'explanation': self.cleaned_data.get(f'question_{i}_explanation', '')
            }
            
            # Add options for multiple choice questions
            if question['type'] == 'multiple_choice':
                options = []
                j = 0
                while f'question_{i}_option_{j}' in self.cleaned_data:
                    option = self.cleaned_data[f'question_{i}_option_{j}']
                    if option.strip():
                        options.append(option.strip())
                    j += 1
                question['options'] = options
            
            questions.append(question)
            i += 1
        
        return questions