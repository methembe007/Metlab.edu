def user_role_context(request):
    """
    Context processor to add user role information to all templates
    """
    context = {}
    
    if request.user.is_authenticated:
        context.update({
            'user_role': getattr(request.user, 'role', None),
            'is_student': getattr(request.user, 'role', None) == 'student',
            'is_teacher': getattr(request.user, 'role', None) == 'teacher',
            'is_parent': getattr(request.user, 'role', None) == 'parent',
        })
    
    return context