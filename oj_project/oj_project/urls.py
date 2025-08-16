# oj_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.shortcuts import render, redirect

def home_view(request):
    """Home page view that renders the landing page"""
    try:
        return render(request, 'landing.html')
    except:
        return HttpResponse("<h1>Django is Working!</h1><p>Landing page template not found, but server is running.</p>")

def test_view(request):
    """Simple test view"""
    return HttpResponse("""
    <h1>Django is Working!</h1>
    <p>Server is running successfully</p>
    <ul>
        <li><a href="/">Home (Landing Page)</a></li>
        <li><a href="/auth/login/">Login</a></li>
        <li><a href="/auth/register/">Register</a></li>
        <li><a href="/problems/">Problems</a></li>
        <li><a href="/django-admin/">Django Admin</a></li>
        <li><a href="/manage/">Custom Admin Dashboard</a></li>
        <li><a href="/emergency-migrate/">🚨 Emergency Migrate (Admin Only)</a></li>
    </ul>
    """)

# Emergency migration view
def emergency_migrate(request):
    """Emergency migration runner"""
    if not request.user.is_superuser:
        return HttpResponse("❌ Access denied. Admin access required.", status=403)
    
    from django.core.management import call_command
    from django.db import connection
    from io import StringIO
    
    output = StringIO()
    
    try:
        output.write("🚨 EMERGENCY MIGRATION STARTED\n\n")
        
        # Show migration status
        output.write("=== CURRENT MIGRATION STATUS ===\n")
        call_command('showmigrations', stdout=output, verbosity=1)
        
        # Run migrations
        output.write("\n=== APPLYING MIGRATIONS ===\n")
        call_command('migrate', stdout=output, verbosity=2)
        
        # Test database
        output.write("\n=== DATABASE VERIFICATION ===\n")
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM auth_user")
            user_count = cursor.fetchone()[0]
            output.write(f"✅ auth_user table accessible, {user_count} users found\n")
        
        output.write("\n✅ EMERGENCY MIGRATION COMPLETED!")
        
    except Exception as e:
        output.write(f"\n❌ MIGRATION FAILED: {str(e)}")
    
    return HttpResponse(f"<pre>{output.getvalue()}</pre>")

urlpatterns = [
    # IMPORTANT: Put specific paths BEFORE the catch-all admin path
    path('test/', test_view, name='test'),
    path('emergency-migrate/', emergency_migrate, name='emergency_migrate'),
    path('', home_view, name='home'),
    
    # Authentication URLs
    path('auth/', include('authentication.urls')),
    
    # Core app URLs (problems, submissions, etc.)
    path('django-admin/', admin.site.urls),
    path('problems/', include('core.urls')),
    
    # Custom Admin Dashboard - use different path to avoid conflict
    path('manage/', include('core.urls')),  # This will make admin dashboard available at /manage/admin/dashboard/
    
    # Compiler URLs
    path('compiler/', include('compiler.urls')),
    
    # Django built-in admin - keep this LAST
      # Changed from 'admin/' to 'django-admin/'
]

# oj_project/urls.py
