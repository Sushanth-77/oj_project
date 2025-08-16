# core/admin_utils.py
from django.shortcuts import redirect
from django.contrib import messages

def redirect_admin_after_login(user, request):
    """
    Helper function to redirect admin users to appropriate dashboard
    """
    if user.is_superuser or user.is_staff:
        messages.info(request, f'Welcome to Admin Panel, {user.username}!')
        return redirect('core:admin_dashboard')
    else:
        return redirect('core:problems_list')

def check_admin_access(user):
    """
    Check if user has admin access
    """
    return user.is_authenticated and (user.is_superuser or user.is_staff)