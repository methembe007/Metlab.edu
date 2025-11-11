#!/usr/bin/env python
"""
Simple login test for teachers
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'metlab_edu.settings')
django.setup()

from django.test import Client
from django.urls import reverse

def test_teacher_login():
    client = Client()
    
    # Test accounts
    accounts = [
        {'username': 'Jameson', 'password': 'your_actual_password'},
        {'username': 'test_teacher', 'password': 'testpass123'}
    ]
    
    for account in accounts:
        print(f"\n--- Testing {account['username']} ---")
        
        # Try login
        response = client.post('/accounts/login/', {
            'username': account['username'],
            'password': account['password']
        })
        
        if response.status_code == 302:  # Redirect means success
            print(f"✓ Login successful for {account['username']}")
            
            # Try accessing teacher dashboard
            response = client.get('/accounts/dashboard/')
            print(f"  Dashboard access: {response.status_code}")
            
        else:
            print(f"✗ Login failed for {account['username']}")
            print(f"  Status: {response.status_code}")

if __name__ == '__main__':
    print("=== Teacher Login Test ===")
    test_teacher_login()
    print("\nNote: Replace 'your_actual_password' with the password you used when registering Jameson")