"""
Simple test to verify navbar template renders correctly for all roles
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'metlab_edu.settings')
django.setup()

from django.template.loader import render_to_string
from django.test import RequestFactory
from django.contrib.auth import get_user_model

User = get_user_model()

def test_navbar_template(role_name):
    """Test navbar template rendering for a specific role"""
    print(f"\n{'='*60}")
    print(f"Testing navbar template for: {role_name.upper()}")
    print('='*60)
    
    # Create test user
    username = f"test_{role_name}_nav"
    User.objects.filter(username=username).delete()
    
    user = User.objects.create_user(
        username=username,
        email=f"{username}@test.com",
        password='testpass123',
        role=role_name,
        first_name=role_name.title()
    )
    
    # Create mock request
    factory = RequestFactory()
    request = factory.get('/')
    request.user = user
    
    # Get context from context processor
    from accounts.context_processors import user_role_context
    context = user_role_context(request)
    context['user'] = user
    context['request'] = request
    
    print(f"✓ User: {user.username} (role: {user.role})")
    print(f"✓ Context variables:")
    print(f"  - user_role: {context.get('user_role')}")
    print(f"  - is_student: {context.get('is_student')}")
    print(f"  - is_teacher: {context.get('is_teacher')}")
    print(f"  - is_parent: {context.get('is_parent')}")
    
    # Try to render base template
    try:
        html = render_to_string('base.html', context, request=request)
        
        # Check for key navbar elements
        checks = {
            'Logo present': 'Metlab.edu' in html,
            'Dashboard link': 'Dashboard' in html,
            'Logout button': 'Logout' in html,
            'Mobile hamburger': 'hamburger-btn' in html,
            'Mobile dropdown': 'mobile-dropdown' in html,
            'Role badge': role_name.title() in html,
            'Navigation script': 'toggleMobileNav' in html,
        }
        
        # Role-specific checks
        if role_name == 'student':
            checks['Library link'] = 'Library' in html
            checks['Upload link'] = 'Upload' in html
            checks['Tutors link'] = 'Tutors' in html
            checks['Achievements link'] = 'Achievements' in html
            checks['Shop link'] = 'Shop' in html
        elif role_name == 'teacher':
            checks['Library link'] = 'Library' in html
            checks['Upload link'] = 'Upload' in html
            checks['My Classes link'] = 'My Classes' in html
        elif role_name == 'parent':
            checks['Children link'] = 'Children' in html
        
        print(f"\n✓ Template rendered successfully")
        print(f"\nNavbar elements check:")
        
        all_passed = True
        for check_name, result in checks.items():
            status = "✓" if result else "✗"
            print(f"  {status} {check_name}")
            if not result:
                all_passed = False
        
        if all_passed:
            print(f"\n✅ All checks passed for {role_name}!")
        else:
            print(f"\n⚠️  Some checks failed for {role_name}")
            
    except Exception as e:
        print(f"✗ Error rendering template: {e}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    user.delete()

def main():
    print("\n" + "="*60)
    print("NAVBAR TEMPLATE RENDERING TEST")
    print("="*60)
    
    roles = ['student', 'teacher', 'parent']
    
    for role in roles:
        try:
            test_navbar_template(role)
        except Exception as e:
            print(f"\n✗ Error testing {role}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETE")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
