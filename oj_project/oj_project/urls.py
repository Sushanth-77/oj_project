# oj_project/urls.py - Updated with separated apps
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication URLs
    path('home/', include('authentication.urls')),
    
    # Compiler/AI review URLs  
    path('compiler/', include('compiler.urls')),
    
    # Core URLs (includes root redirect and main functionality)
    path('', include('core.urls')),
]