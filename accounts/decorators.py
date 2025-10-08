from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def role_required(required_role):
    """
    Decorator to restrict access to views based on user role
    
    Usage:
        @role_required('student')
        def student_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not hasattr(request.user, 'role'):
                messages.error(request, 'User role not found.')
                return redirect('login')
            
            if request.user.role != required_role:
                messages.error(
                    request, 
                    f'Access denied. {required_role.title()} account required.'
                )
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def student_required(view_func):
    """Decorator to restrict access to student users only"""
    return role_required('student')(view_func)


def teacher_required(view_func):
    """Decorator to restrict access to teacher users only"""
    return role_required('teacher')(view_func)


def parent_required(view_func):
    """Decorator to restrict access to parent users only"""
    return role_required('parent')(view_func)


def profile_required(view_func):
    """
    Decorator to ensure user has the appropriate profile for their role
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        
        # Check if user has appropriate profile
        try:
            if user.role == 'student' and not hasattr(user, 'student_profile'):
                messages.error(request, 'Student profile not found.')
                return redirect('dashboard')
            elif user.role == 'teacher' and not hasattr(user, 'teacher_profile'):
                messages.error(request, 'Teacher profile not found.')
                return redirect('dashboard')
            elif user.role == 'parent' and not hasattr(user, 'parent_profile'):
                messages.error(request, 'Parent profile not found.')
                return redirect('dashboard')
        except AttributeError:
            messages.error(request, 'User profile error.')
            return redirect('login')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view