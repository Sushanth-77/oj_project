# oj_project/oj_project/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Include core URLs - this includes the root redirect and all other URLs
    path('', include('core.urls')),
]