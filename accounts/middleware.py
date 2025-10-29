from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


class RoleBasedAccessMiddleware(MiddlewareMixin):
    """
    Middleware to enforce role-based access control for specific views
    """
    
    # Define role-specific URL patterns
    ROLE_RESTRICTED_URLS = {
        'student': [
            '/accounts/dashboard/student/',
        ],
        'teacher': [
            '/accounts/dashboard/teacher/',
        ],
        'parent': [
            '/accounts/dashboard/parent/',
        ]
    }
    
    def process_request(self, request):
        # Skip middleware for non-authenticated users
        if not request.user.is_authenticated:
            return None
        
        # Skip middleware for superusers
        if request.user.is_superuser:
            return None
        
        current_path = request.path
        user_role = getattr(request.user, 'role', None)
        
        # Check if current path is role-restricted
        for role, restricted_urls in self.ROLE_RESTRICTED_URLS.items():
            if current_path in restricted_urls:
                if user_role != role:
                    messages.error(
                        request, 
                        f'Access denied. {role.title()} account required.'
                    )
                    return redirect('accounts:dashboard')
        
        return None