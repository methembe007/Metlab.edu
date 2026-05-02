#!/usr/bin/env python
"""
Diagnostic script to check PDF preview functionality
Run this to identify why PDF previews might not be displaying
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'metlab_edu.settings')
django.setup()

from learning.teacher_models import TeacherContent
from content.models import UploadedContent
from django.contrib.auth.models import User

def diagnose_pdf_preview():
    print("=" * 60)
    print("PDF PREVIEW DIAGNOSTIC REPORT")
    print("=" * 60)
    print()
    
    # Check 1: Are there any PDF files in the system?
    print("1. Checking for PDF files in the system...")
    pdf_contents = UploadedContent.objects.filter(content_type='pdf')
    print(f"   Found {pdf_contents.count()} PDF files")
    
    if pdf_contents.exists():
        print("\n   PDF Files:")
        for pdf in pdf_contents[:5]:  # Show first 5
            print(f"   - {pdf.original_filename}")
            print(f"     File exists: {pdf.file and os.path.exists(pdf.file.path)}")
            if pdf.file:
                print(f"     Path: {pdf.file.path}")
                if os.path.exists(pdf.file.path):
                    size = os.path.getsize(pdf.file.path)
                    print(f"     Size: {size:,} bytes ({size/1024/1024:.2f} MB)")
            print()
    else:
        print("   ⚠️  NO PDF FILES FOUND!")
        print("   → Upload a PDF file first to test the preview functionality")
    
    print()
    
    # Check 2: Are there any TeacherContent entries with PDFs?
    print("2. Checking for teacher-assigned PDF content...")
    teacher_pdfs = TeacherContent.objects.filter(
        uploaded_content__content_type='pdf'
    ).select_related('uploaded_content', 'teacher__user')
    
    print(f"   Found {teacher_pdfs.count()} teacher-assigned PDFs")
    
    if teacher_pdfs.exists():
        print("\n   Teacher PDF Assignments:")
        for tc in teacher_pdfs[:5]:  # Show first 5
            print(f"   - {tc.title}")
            print(f"     Teacher: {tc.teacher.user.get_full_name() or tc.teacher.user.username}")
            print(f"     Subject: {tc.subject}")
            print(f"     Assigned to {tc.assigned_classes.count()} class(es)")
            print(f"     File: {tc.uploaded_content.original_filename}")
            print()
    else:
        print("   ⚠️  NO TEACHER-ASSIGNED PDFs FOUND!")
        print("   → Teachers need to upload and assign PDFs to classes")
    
    print()
    
    # Check 3: Check student enrollments
    print("3. Checking student enrollments...")
    from learning.teacher_models import ClassEnrollment
    enrollments = ClassEnrollment.objects.filter(is_active=True)
    print(f"   Found {enrollments.count()} active student enrollments")
    
    if enrollments.exists():
        print("\n   Sample enrollments:")
        for enrollment in enrollments[:3]:
            print(f"   - {enrollment.student.user.username} in {enrollment.teacher_class.name}")
    else:
        print("   ⚠️  NO ACTIVE ENROLLMENTS!")
        print("   → Students need to enroll in classes to see content")
    
    print()
    
    # Check 4: Check media file configuration
    print("4. Checking media file configuration...")
    from django.conf import settings
    
    print(f"   MEDIA_ROOT: {settings.MEDIA_ROOT}")
    print(f"   MEDIA_URL: {settings.MEDIA_URL}")
    
    if os.path.exists(settings.MEDIA_ROOT):
        print(f"   ✓ MEDIA_ROOT directory exists")
        
        # Check for uploaded files
        uploads_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        if os.path.exists(uploads_dir):
            files = []
            for root, dirs, filenames in os.walk(uploads_dir):
                for filename in filenames:
                    if filename.endswith('.pdf'):
                        files.append(os.path.join(root, filename))
            
            print(f"   Found {len(files)} PDF file(s) in uploads directory")
            if files:
                print("\n   PDF Files on disk:")
                for f in files[:5]:
                    size = os.path.getsize(f)
                    print(f"   - {os.path.basename(f)} ({size:,} bytes)")
        else:
            print(f"   ⚠️  Uploads directory doesn't exist: {uploads_dir}")
    else:
        print(f"   ⚠️  MEDIA_ROOT directory doesn't exist!")
    
    print()
    
    # Check 5: Test URL generation
    print("5. Testing URL generation...")
    if teacher_pdfs.exists():
        test_content = teacher_pdfs.first()
        from django.urls import reverse
        try:
            url = reverse('learning:view_pdf', args=[test_content.id])
            print(f"   ✓ PDF view URL: {url}")
            
            download_url = reverse('learning:download_content', args=[test_content.id])
            print(f"   ✓ Download URL: {download_url}")
        except Exception as e:
            print(f"   ✗ Error generating URLs: {e}")
    else:
        print("   ⚠️  No PDFs available to test URL generation")
    
    print()
    
    # Summary and recommendations
    print("=" * 60)
    print("SUMMARY & RECOMMENDATIONS")
    print("=" * 60)
    print()
    
    issues = []
    
    if not pdf_contents.exists():
        issues.append("No PDF files uploaded - Upload PDFs via teacher dashboard")
    
    if not teacher_pdfs.exists():
        issues.append("No PDFs assigned to classes - Teachers need to assign content")
    
    if not enrollments.exists():
        issues.append("No student enrollments - Students need to join classes")
    
    if not os.path.exists(settings.MEDIA_ROOT):
        issues.append("MEDIA_ROOT directory missing - Check Django settings")
    
    if issues:
        print("⚠️  Issues found:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
    else:
        print("✓ All checks passed!")
        print()
        print("If PDF preview still doesn't work, check:")
        print("   1. Browser console for JavaScript errors")
        print("   2. Network tab to see if PDF loads (200 status)")
        print("   3. Browser PDF viewer settings")
        print("   4. Try different browsers (Chrome, Firefox, Edge)")
        print("   5. Check if browser blocks iframes or PDFs")
    
    print()
    print("=" * 60)

if __name__ == '__main__':
    diagnose_pdf_preview()
