"""
Test script to verify navbar works for all user roles
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'metlab_edu.settings')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth import get_user_model
from django.template import Template, Context
from django.template.loader import render_to_string

User = get_user_model()

def test_navbar_for_role(role_name):
    """Test navbar rendering for a specific role"""
    print(f"\n{'='*60}")
    print(f"Testing navbar for role: {role_name.upper()}")
    print('='*60)
    
    # Create test user
    username = f"test_{role_name}"
    email = f"{username}@test.com"
    
    # Clean up existing test user
    User.objects.filter(username=username).delete()
    
    # Create user with role
    user = User.objects.create_user(
        username=username,
        email=email,
        password='testpass123',
        role=role_name,
        first_name=role_name.title()
    )
    
    # Create request factory
    factory = RequestFactory()
    request = factory.get('/')
    request.user = user
    
    # Test context processor
    from accounts.context_processors import user_role_context
    context = user_role_context(request)
    
    print(f"✓ User created: {user.username}")
    print(f"✓ User role: {user.role}")
    print(f"✓ Context processor output:")
    for key, value in context.items():
        print(f"  - {key}: {value}")
    
    # Test with Django client
    client = Client()
    logged_in = client.login(username=username, password='testpass123')
    
    if logged_in:
        print(f"✓ Login successful")
        
        # Test dashboard access
        try:
            response = client.get('/accounts/dashboard/')
            print(f"✓ Dashboard accessible (Status: {response.status_code})")
            
            # Check if navbar elements are in response
            content = response.content.decode('utf-8')
            
            checks = {
                'Logo': 'Metlab.edu' in content,
                'Dashboard link': 'Dashboard' in content,
                'Logout button': 'Logout' in content,
                'Mobile menu': 'hamburger-btn' in content,
                'Role badge': role_name.title() in content,
            }
            
            # Role-specific checks
            if role_name == 'student':
                checks['Tutors link'] = 'Tutors' in content
                checks['Achievements link'] = 'Achievements' in content
                checks['Shop link'] = 'Shop' in content
            elif role_name == 'teacher':
                checks['My Classes link'] = 'My Classes' in content or 'teacher_dashboard' in content
            elif role_name == 'parent':
                checks['Children link'] = 'Children' in content or 'parent_dashboard' in content
            
            print(f"\n  Navbar elements check:")
            for check_name, result in checks.items():
                status = "✓" if result else "✗"
                print(f"    {status} {check_name}")
                
        except Exception as e:
            print(f"✗ Error accessing dashboard: {e}")
    else:
        print(f"✗ Login failed")
    
    # Cleanup
    user.delete()
    print(f"\n✓ Test user cleaned up")

def main():
    print("\n" + "="*60)
    print("NAVBAR FUNCTIONALITY TEST - ALL USER ROLES")
    print("="*60)
    
    roles = ['student', 'teacher', 'parent']
    
    for role in roles:
        try:
            test_navbar_for_role(role)
        except Exception as e:
            print(f"\n✗ Error testing {role}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
