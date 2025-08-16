# authentication/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.contrib.auth.decorators import user_passes_test
from django.core.management import call_command
from django.db import connection
from io import StringIO
import sys

def is_superuser(user):
    return user.is_authenticated and user.is_superuser

@user_passes_test(is_superuser)
def run_migrations_now(request):
    """Emergency migration runner - only for superusers"""
    
    output = StringIO()
    
    try:
        # Show current migration status
        output.write("=== MIGRATION STATUS ===\n")
        call_command('showmigrations', stdout=output, verbosity=2)
        
        # Run migrations
        output.write("\n=== RUNNING MIGRATIONS ===\n")
        call_command('migrate', stdout=output, verbosity=2)
        
        # Verify auth_user table
        output.write("\n=== VERIFICATION ===\n")
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            tables = cursor.fetchall()
            output.write(f"Database tables: {[t[0] for t in tables]}\n")
            
            # Check if auth_user exists
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'auth_user'
            """)
            auth_user_exists = cursor.fetchone()[0] > 0
            output.write(f"auth_user table exists: {auth_user_exists}\n")
            
            if auth_user_exists:
                from django.contrib.auth.models import User
                user_count = User.objects.count()
                output.write(f"User count: {user_count}\n")
        
        output.write("\n✅ Migration completed successfully!")
        
    except Exception as e:
        output.write(f"\n❌ Error during migration: {str(e)}")
        
    return HttpResponse(f"<pre>{output.getvalue()}</pre>", content_type="text/html")

def register_user(request):
    """User registration view"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, 'Username and password are required')
            return redirect("/auth/register/")

        if len(username) < 3:
            messages.error(request, 'Username must be at least 3 characters long')
            return redirect("/auth/register/")
            
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long')
            return redirect("/auth/register/")

        if User.objects.filter(username=username).exists():
            messages.error(request, 'User with this username already exists')
            return redirect("/auth/register/")
        
        try:
            User.objects.create_user(username=username, password=password)
            messages.success(request, 'User created successfully. Please login.')
            return redirect('/auth/login/')
        except Exception as e:
            messages.error(request, f'Error creating user: {str(e)}')
            return redirect("/auth/register/")

    return render(request, 'register.html')

def login_user(request):
    """User login view with admin redirection"""
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, 'Username and password are required')
            return redirect('/auth/login/')

        if not User.objects.filter(username=username).exists():
            messages.error(request, 'User with this username does not exist')
            return redirect('/auth/login/')
        
        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, 'Invalid password')
            return redirect('/auth/login/')
        
        login(request, user)
        
        # Check if user is admin/superuser and redirect accordingly
        if user.is_superuser or user.is_staff:
            messages.success(request, f'Welcome back, Admin {user.username}!')
            return redirect('/problems/admin/dashboard/')  # Redirect to admin dashboard
        else:
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('/problems/')  # Regular users go to problems list
    
    return render(request, 'login.html')

def logout_user(request):
    """Logout user and redirect"""
    logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('/auth/login/')