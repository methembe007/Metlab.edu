#!/usr/bin/env python
"""
Simple script to test teacher login functionality
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'metlab_edu.settings')
django.setup()

from django.contrib.auth import get_user_model, authenticate
from django.test import Client
from django.urls import reverse

User = get_user_model()

def test_teacher_login():
    """Test teacher login functionality"""
    
    # Check if Jameson user exists and is properly configured
    try:
        user = User.objects.get(username='Jameson')
        print(f"✓ User found: {user.username}")
        print(f"  - Role: {user.role}")
        print(f"  - Active: {user.is_active}")
        print(f"  - Email verified: {user.email_verified}")
        print(f"  - Has teacher profile: {hasattr(user, 'teacher_profile')}")
        
        if hasattr(user, 'teacher_profile'):
            print(f"  - Teacher profile: {user.teacher_profile}")
        
    except User.DoesNotExist:
        print("✗ User 'Jameson' not found")
        return False
    
    # Test authentication
    print("\n--- Testing Authentication ---")
    auth_user = authenticate(username='Jameson', password='your_password_here')
    if auth_user:
        print("✓ Authentication successful")
    else:
        print("✗ Authentication failed - check password")
        return False
    
    # Test URL resolution
    print("\n--- Testing URL Resolution ---")
    try:
        dashboard_url = reverse('learning:teacher_content_dashboard')
        print(f"✓ Teacher dashboard URL resolves to: {dashboard_url}")
    except Exception as e:
        print(f"✗ URL resolution failed: {e}")
        return False
    
    # Test client login
    print("\n--- Testing Client Login ---")
    client = Client()
    
    # Try to access teacher dashboard without login (should redirect)
    response = client.get(dashboard_url)
    print(f"  - Unauthenticated access status: {response.status_code}")
    
    # Login and try again
    login_success = client.login(username='Jameson', password='your_password_here')
    if login_success:
        print("✓ Client login successful")
        
        # Try to access dashboard
        response = client.get(dashboard_url)
        print(f"  - Authenticated access status: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Teacher dashboard accessible")
        else:
            print(f"✗ Teacher dashboard not accessible (status: {response.status_code})")
            
    else:
        print("✗ Client login failed")
        return False
    
    return True

if __name__ == '__main__':
    print("=== Teacher Login Test ===\n")
    
    success = test_teacher_login()
    
    if success:
        print("\n✓ All tests passed! Teacher login should work.")
    else:
        print("\n✗ Some tests failed. Check the issues above.")
        
    print("\nNote: Replace 'your_password_here' with the actual password you used during registration.")