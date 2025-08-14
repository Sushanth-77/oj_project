# oj_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.shortcuts import render, redirect

def home_view(request):
    """Home page view that renders the landing page"""
    return render(request, 'landing.html')

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
        <li><a href="/admin/">Admin</a></li>
    </ul>
    """)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('test/', test_view, name='test'),
    path('', home_view, name='home'),  # Root URL shows landing page
    
    # Authentication URLs
    path('auth/', include('authentication.urls')),
    
    # Core app URLs (problems, submissions, etc.)
    path('problems/', include('core.urls')),  # This will handle /problems/ URLs
    
    # Compiler URLs
    path('compiler/', include('compiler.urls')),
]