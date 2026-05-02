"""
Test suite for PDF viewing functionality
Ensures teachers can upload PDFs and students can view them
"""
import os
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from accounts.models import TeacherProfile, StudentProfile
from learning.teacher_models import TeacherClass, ClassEnrollment, TeacherContent
from content.models import UploadedContent

User = get_user_model()


class PDFViewingTestCase(TestCase):
    """Test PDF upload and viewing functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create teacher user and profile
        self.teacher_user = User.objects.create_user(
            username='teacher1',
            email='teacher@test.com',
            password='testpass123',
            role='teacher'
        )
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            subject_specialization='Mathematics',
            years_of_experience=5
        )
        
        # Create student user and profile
        self.student_user = User.objects.create_user(
            username='student1',
            email='student@test.com',
            password='testpass123',
            role='student'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            grade_level=10
        )
        
        # Create a class
        self.teacher_class = TeacherClass.objects.create(
            teacher=self.teacher_profile,
            name='Math 101',
            subject='Mathematics',
            grade_level=10
        )
        
        # Enroll student in class
        self.enrollment = ClassEnrollment.objects.create(
            teacher_class=self.teacher_class,
            student=self.student_profile
        )
        
        # Create a mock PDF file
        self.pdf_content = b'%PDF-1.4 Mock PDF content for testing'
        self.pdf_file = SimpleUploadedFile(
            'test_document.pdf',
            self.pdf_content,
            content_type='application/pdf'
        )
        
        self.client = Client()
    
    def test_teacher_can_upload_pdf(self):
        """Test that teachers can upload PDF files"""
        self.client.login(username='teacher1', password='testpass123')
        
        # Upload PDF
        response = self.client.post(
            reverse('learning:upload_content'),
            {
                'file': self.pdf_file,
                'title': 'Test PDF Document',
                'subject': 'Mathematics',
                'description': 'A test PDF for students',
            }
        )
        
        # Check redirect (successful upload)
        self.assertEqual(response.status_code, 302)
        
        # Verify content was created
        self.assertTrue(TeacherContent.objects.filter(title='Test PDF Document').exists())
        teacher_content = TeacherContent.objects.get(title='Test PDF Document')
        self.assertEqual(teacher_content.uploaded_content.content_type, 'pdf')
    
    def test_teacher_can_assign_pdf_to_class(self):
        """Test that teachers can assign PDFs to classes"""
        # Create uploaded content
        uploaded_content = UploadedContent.objects.create(
            user=self.teacher_user,
            file=self.pdf_file,
            original_filename='test.pdf',
            content_type='pdf',
            file_size=len(self.pdf_content)
        )
        
        # Create teacher content
        teacher_content = TeacherContent.objects.create(
            teacher=self.teacher_profile,
            uploaded_content=uploaded_content,
            title='Assigned PDF',
            subject='Mathematics',
            description='PDF for class'
        )
        
        # Assign to class
        teacher_content.assigned_classes.add(self.teacher_class)
        
        # Verify assignment
        self.assertIn(self.teacher_class, teacher_content.assigned_classes.all())
    
    def test_student_can_see_assigned_pdf(self):
        """Test that students can see PDFs assigned to their class"""
        # Create and assign content
        uploaded_content = UploadedContent.objects.create(
            user=self.teacher_user,
            file=self.pdf_file,
            original_filename='test.pdf',
            content_type='pdf',
            file_size=len(self.pdf_content)
        )
        
        teacher_content = TeacherContent.objects.create(
            teacher=self.teacher_profile,
            uploaded_content=uploaded_content,
            title='Student PDF',
            subject='Mathematics',
            description='PDF for students'
        )
        teacher_content.assigned_classes.add(self.teacher_class)
        
        # Login as student
        self.client.login(username='student1', password='testpass123')
        
        # Access class content page
        response = self.client.get(
            reverse('learning:class_content', kwargs={'class_id': self.teacher_class.id})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Student PDF')
        self.assertContains(response, 'View PDF')
    
    def test_student_can_view_pdf_detail(self):
        """Test that students can view PDF detail page"""
        # Create and assign content
        uploaded_content = UploadedContent.objects.create(
            user=self.teacher_user,
            file=self.pdf_file,
            original_filename='test.pdf',
            content_type='pdf',
            file_size=len(self.pdf_content)
        )
        
        teacher_content = TeacherContent.objects.create(
            teacher=self.teacher_profile,
            uploaded_content=uploaded_content,
            title='Detail PDF',
            subject='Mathematics',
            description='PDF detail test'
        )
        teacher_content.assigned_classes.add(self.teacher_class)
        
        # Login as student
        self.client.login(username='student1', password='testpass123')
        
        # Access content detail page
        response = self.client.get(
            reverse('learning:view_content', kwargs={'content_id': teacher_content.id})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Detail PDF')
        self.assertContains(response, 'View PDF')
        self.assertContains(response, 'Download')
    
    def test_student_can_access_pdf_viewer(self):
        """Test that students can access the PDF viewer endpoint"""
        # Create and assign content
        uploaded_content = UploadedContent.objects.create(
            user=self.teacher_user,
            file=self.pdf_file,
            original_filename='test.pdf',
            content_type='pdf',
            file_size=len(self.pdf_content)
        )
        
        teacher_content = TeacherContent.objects.create(
            teacher=self.teacher_profile,
            uploaded_content=uploaded_content,
            title='Viewer PDF',
            subject='Mathematics'
        )
        teacher_content.assigned_classes.add(self.teacher_class)
        
        # Login as student
        self.client.login(username='student1', password='testpass123')
        
        # Access PDF viewer
        response = self.client.get(
            reverse('learning:view_pdf', kwargs={'content_id': teacher_content.id})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('inline', response['Content-Disposition'])
    
    def test_student_can_download_pdf(self):
        """Test that students can download PDFs"""
        # Create and assign content
        uploaded_content = UploadedContent.objects.create(
            user=self.teacher_user,
            file=self.pdf_file,
            original_filename='test.pdf',
            content_type='pdf',
            file_size=len(self.pdf_content)
        )
        
        teacher_content = TeacherContent.objects.create(
            teacher=self.teacher_profile,
            uploaded_content=uploaded_content,
            title='Download PDF',
            subject='Mathematics'
        )
        teacher_content.assigned_classes.add(self.teacher_class)
        
        # Login as student
        self.client.login(username='student1', password='testpass123')
        
        # Download PDF
        response = self.client.get(
            reverse('learning:download_content', kwargs={'content_id': teacher_content.id})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response['Content-Disposition'])
    
    def test_student_cannot_access_unassigned_pdf(self):
        """Test that students cannot access PDFs not assigned to their class"""
        # Create content but don't assign to class
        uploaded_content = UploadedContent.objects.create(
            user=self.teacher_user,
            file=self.pdf_file,
            original_filename='test.pdf',
            content_type='pdf',
            file_size=len(self.pdf_content)
        )
        
        teacher_content = TeacherContent.objects.create(
            teacher=self.teacher_profile,
            uploaded_content=uploaded_content,
            title='Unassigned PDF',
            subject='Mathematics'
        )
        # Note: NOT assigned to any class
        
        # Login as student
        self.client.login(username='student1', password='testpass123')
        
        # Try to access content
        response = self.client.get(
            reverse('learning:view_content', kwargs={'content_id': teacher_content.id})
        )
        
        # Should redirect with error message
        self.assertEqual(response.status_code, 302)
    
    def test_unauthenticated_user_cannot_view_pdf(self):
        """Test that unauthenticated users cannot view PDFs"""
        # Create and assign content
        uploaded_content = UploadedContent.objects.create(
            user=self.teacher_user,
            file=self.pdf_file,
            original_filename='test.pdf',
            content_type='pdf',
            file_size=len(self.pdf_content)
        )
        
        teacher_content = TeacherContent.objects.create(
            teacher=self.teacher_profile,
            uploaded_content=uploaded_content,
            title='Protected PDF',
            subject='Mathematics'
        )
        teacher_content.assigned_classes.add(self.teacher_class)
        
        # Try to access without login
        response = self.client.get(
            reverse('learning:view_pdf', kwargs={'content_id': teacher_content.id})
        )
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_pdf_viewer_embedded_in_detail_page(self):
        """Test that PDF viewer is embedded in the detail page"""
        # Create and assign content
        uploaded_content = UploadedContent.objects.create(
            user=self.teacher_user,
            file=self.pdf_file,
            original_filename='test.pdf',
            content_type='pdf',
            file_size=len(self.pdf_content)
        )
        
        teacher_content = TeacherContent.objects.create(
            teacher=self.teacher_profile,
            uploaded_content=uploaded_content,
            title='Embedded PDF',
            subject='Mathematics'
        )
        teacher_content.assigned_classes.add(self.teacher_class)
        
        # Login as student
        self.client.login(username='student1', password='testpass123')
        
        # Access content detail page
        response = self.client.get(
            reverse('learning:view_content', kwargs={'content_id': teacher_content.id})
        )
        
        self.assertEqual(response.status_code, 200)
        # Check for iframe with PDF viewer
        self.assertContains(response, '<iframe')
        self.assertContains(response, 'Document Preview')
    
    def test_all_content_page_shows_pdfs(self):
        """Test that the all content page shows PDFs"""
        # Create and assign content
        uploaded_content = UploadedContent.objects.create(
            user=self.teacher_user,
            file=self.pdf_file,
            original_filename='test.pdf',
            content_type='pdf',
            file_size=len(self.pdf_content)
        )
        
        teacher_content = TeacherContent.objects.create(
            teacher=self.teacher_profile,
            uploaded_content=uploaded_content,
            title='All Content PDF',
            subject='Mathematics'
        )
        teacher_content.assigned_classes.add(self.teacher_class)
        
        # Login as student
        self.client.login(username='student1', password='testpass123')
        
        # Access all content page
        response = self.client.get(reverse('learning:all_assigned_content'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'All Content PDF')
        self.assertContains(response, 'PDF')


class PDFAccessControlTestCase(TestCase):
    """Test access control for PDF viewing"""
    
    def setUp(self):
        """Set up test data"""
        # Create teacher
        self.teacher_user = User.objects.create_user(
            username='teacher1',
            email='teacher@test.com',
            password='testpass123',
            role='teacher'
        )
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            subject_specialization='Mathematics'
        )
        
        # Create two students
        self.student1_user = User.objects.create_user(
            username='student1',
            email='student1@test.com',
            password='testpass123',
            role='student'
        )
        self.student1_profile = StudentProfile.objects.create(
            user=self.student1_user,
            grade_level=10
        )
        
        self.student2_user = User.objects.create_user(
            username='student2',
            email='student2@test.com',
            password='testpass123',
            role='student'
        )
        self.student2_profile = StudentProfile.objects.create(
            user=self.student2_user,
            grade_level=10
        )
        
        # Create two classes
        self.class1 = TeacherClass.objects.create(
            teacher=self.teacher_profile,
            name='Class A',
            subject='Mathematics'
        )
        
        self.class2 = TeacherClass.objects.create(
            teacher=self.teacher_profile,
            name='Class B',
            subject='Mathematics'
        )
        
        # Enroll student1 in class1 only
        ClassEnrollment.objects.create(
            teacher_class=self.class1,
            student=self.student1_profile
        )
        
        # Enroll student2 in class2 only
        ClassEnrollment.objects.create(
            teacher_class=self.class2,
            student=self.student2_profile
        )
        
        self.client = Client()
    
    def test_student_can_only_view_pdfs_from_their_classes(self):
        """Test that students can only view PDFs assigned to their classes"""
        # Create PDF for class1
        pdf_file = SimpleUploadedFile(
            'class1.pdf',
            b'%PDF-1.4 Class 1 PDF',
            content_type='application/pdf'
        )
        
        uploaded_content = UploadedContent.objects.create(
            user=self.teacher_user,
            file=pdf_file,
            original_filename='class1.pdf',
            content_type='pdf',
            file_size=100
        )
        
        teacher_content = TeacherContent.objects.create(
            teacher=self.teacher_profile,
            uploaded_content=uploaded_content,
            title='Class 1 PDF',
            subject='Mathematics'
        )
        teacher_content.assigned_classes.add(self.class1)
        
        # Student1 should be able to access
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(
            reverse('learning:view_pdf', kwargs={'content_id': teacher_content.id})
        )
        self.assertEqual(response.status_code, 200)
        
        # Student2 should NOT be able to access
        self.client.login(username='student2', password='testpass123')
        response = self.client.get(
            reverse('learning:view_pdf', kwargs={'content_id': teacher_content.id})
        )
        self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'metlab_edu.settings')
    django.setup()
    
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['tests.test_pdf_viewing'])
