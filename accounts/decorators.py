from functools import wraps
from django.http import HttpResponseForbidden

def super_admin_required(view_func):
    """Decorator for views that checks if the user is a super admin."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'super_admin':
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden('You do not have permission to access this page.')
    return _wrapped_view

def staff_required(view_func):
    """Decorator for views that checks if the user is staff or higher (including super admin)."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role in ['staff', 'super_admin']:
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden('You do not have permission to access this page.')
    return _wrapped_view

def customer_required(view_func):
    """Decorator for views that checks if the user is a customer."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'customer':
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden('You do not have permission to access this page.')
    return _wrapped_view
