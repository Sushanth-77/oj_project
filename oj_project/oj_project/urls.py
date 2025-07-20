from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('core.urls')),
    # Root URL redirects to auth/register/
    path('', lambda request: redirect('/auth/register/', permanent=False)),
    # Include core URLs at root level for problems, submissions etc.
    path('', include('core.urls')),
]