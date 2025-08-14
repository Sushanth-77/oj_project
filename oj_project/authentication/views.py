# authentication/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
# Add this to the END of your authentication/views.py file

from django.http import HttpResponse
from django.core.management import call_command
from django.contrib.auth.models import User
from django.db import connection
import traceback
import io
import sys

def debug_info(request):
    """Debug view to check database and migrations status"""
    try:
        output = []
        output.append("=== DATABASE DEBUG INFO ===\n")
        
        # Check database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                output.append("✅ Database connection: OK\n")
        except Exception as e:
            output.append(f"❌ Database connection: {str(e)}\n")
        
        # Check if auth_user table exists
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM auth_user")
                count = cursor.fetchone()[0]
                output.append(f"✅ auth_user table exists with {count} users\n")
        except Exception as e:
            output.append(f"❌ auth_user table: {str(e)}\n")
        
        # Check User model
        try:
            user_count = User.objects.count()
            output.append(f"✅ User model works: {user_count} users\n")
        except Exception as e:
            output.append(f"❌ User model: {str(e)}\n")
        
        # Check migrations
        output.append("\n=== MIGRATION STATUS ===\n")
        try:
            old_stdout = sys.stdout
            sys.stdout = buffer = io.StringIO()
            call_command('showmigrations')
            migration_output = buffer.getvalue()
            sys.stdout = old_stdout
            output.append(migration_output)
        except Exception as e:
            output.append(f"Error checking migrations: {str(e)}\n")
        
        # Run migrations if needed
        if request.GET.get('run_migrations') == 'yes':
            output.append("\n=== RUNNING MIGRATIONS ===\n")
            try:
                old_stdout = sys.stdout
                sys.stdout = buffer = io.StringIO()
                call_command('makemigrations')
                call_command('migrate')
                migrate_output = buffer.getvalue()
                sys.stdout = old_stdout
                output.append(migrate_output)
                output.append("✅ Migrations completed!\n")
            except Exception as e:
                output.append(f"❌ Migration error: {str(e)}\n")
        
        return HttpResponse(f"<pre>{''.join(output)}</pre>", content_type='text/html')
        
    except Exception as e:
        return HttpResponse(f"<pre>Debug error: {str(e)}\n\n{traceback.format_exc()}</pre>")

def test_registration(request):
    """Test registration functionality"""
    try:
        output = []
        output.append("=== REGISTRATION TEST ===\n")
        
        # Test if we can create a user
        test_username = "testuser123"
        test_password = "testpass123"
        
        # Check if test user exists
        if User.objects.filter(username=test_username).exists():
            output.append(f"Test user {test_username} already exists\n")
            # Delete for clean test
            User.objects.filter(username=test_username).delete()
            output.append(f"Deleted existing test user\n")
        
        # Try to create user
        try:
            user = User.objects.create_user(username=test_username, password=test_password)
            output.append(f"✅ Successfully created user: {user.username}\n")
            output.append(f"User ID: {user.id}\n")
            
            # Clean up
            user.delete()
            output.append("✅ Test user deleted\n")
            
        except Exception as e:
            output.append(f"❌ Error creating user: {str(e)}\n")
            output.append(f"Full error: {traceback.format_exc()}\n")
        
        return HttpResponse(f"<pre>{''.join(output)}</pre>", content_type='text/html')
        
    except Exception as e:
        return HttpResponse(f"<pre>Test error: {str(e)}\n\n{traceback.format_exc()}</pre>")
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
    """User login view"""
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
        messages.success(request, f'Welcome back, {user.username}!')
        return redirect('/problems/')  # This now correctly points to /problems/
    
    return render(request, 'login.html')

def logout_user(request):
    """Logout user and redirect"""
    logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('/auth/login/')