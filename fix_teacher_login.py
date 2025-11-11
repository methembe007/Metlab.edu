#!/usr/bin/env python
"""
Script to diagnose and fix teacher login issues
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'metlab_edu.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import TeacherProfile

User = get_user_model()

def diagnose_teacher_login():
    """Diagnose teacher login issues"""
    
    print("=== Teacher Login Diagnosis ===\n")
    
    # List all teacher users
    teacher_users = User.objects.filter(role='teacher')
    print(f"Found {teacher_users.count()} teacher users:")
    
    for user in teacher_users:
        print(f"\n--- User: {user.username} ---")
        print(f"  Email: {user.email}")
        print(f"  Active: {user.is_active}")
        print(f"  Email Verified: {user.email_verified}")
        print(f"  Date Joined: {user.date_joined}")
        
        # Check if teacher profile exists
        try:
            teacher_profile = user.teacher_profile
            print(f"  ✓ Teacher Profile exists: {teacher_profile}")
        except TeacherProfile.DoesNotExist:
            print(f"  ✗ No Teacher Profile found")
        
        # Check login issues
        issues = []
        if not user.is_active:
            issues.append("User is not active")
        if not user.email_verified:
            issues.append("Email not verified")
        
        if issues:
            print(f"  Issues: {', '.join(issues)}")
        else:
            print(f"  ✓ No issues found")

def fix_teacher_login(username):
    """Fix common teacher login issues"""
    
    try:
        user = User.objects.get(username=username)
        print(f"\n=== Fixing login for {username} ===")
        
        # Fix common issues
        fixed = []
        
        if not user.is_active:
            user.is_active = True
            fixed.append("Activated user")
        
        if not user.email_verified:
            user.email_verified = True
            fixed.append("Verified email")
        
        # Ensure teacher profile exists
        try:
            teacher_profile = user.teacher_profile
        except TeacherProfile.DoesNotExist:
            teacher_profile = TeacherProfile.objects.create(
                user=user,
                bio="Teacher profile created automatically",
                expertise_areas=['General']
            )
            fixed.append("Created teacher profile")
        
        if fixed:
            user.save()
            print(f"✓ Fixed: {', '.join(fixed)}")
            print(f"✓ {username} should now be able to log in")
        else:
            print(f"✓ No fixes needed for {username}")
            
    except User.DoesNotExist:
        print(f"✗ User '{username}' not found")

def create_test_teacher():
    """Create a test teacher account"""
    
    print("\n=== Creating Test Teacher ===")
    
    username = "testteacher"
    email = "teacher@test.com"
    password = "testpass123"
    
    # Check if user already exists
    if User.objects.filter(username=username).exists():
        print(f"✗ User '{username}' already exists")
        return
    
    # Create user
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        role='teacher',
        first_name='Test',
        last_name='Teacher',
        is_active=True,
        email_verified=True
    )
    
    # Create teacher profile
    teacher_profile = TeacherProfile.objects.create(
        user=user,
        bio="Test teacher account for development",
        expertise_areas=['Math', 'Science']
    )
    
    print(f"✓ Created test teacher account:")
    print(f"  Username: {username}")
    print(f"  Email: {email}")
    print(f"  Password: {password}")
    print(f"  Profile: {teacher_profile}")

if __name__ == '__main__':
    # Diagnose existing issues
    diagnose_teacher_login()
    
    # Ask user what to do
    print("\n" + "="*50)
    print("What would you like to do?")
    print("1. Fix a specific teacher account")
    print("2. Create a test teacher account")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == '1':
        username = input("Enter the teacher username to fix: ").strip()
        if username:
            fix_teacher_login(username)
    elif choice == '2':
        create_test_teacher()
    elif choice == '3':
        print("Exiting...")
    else:
        print("Invalid choice")