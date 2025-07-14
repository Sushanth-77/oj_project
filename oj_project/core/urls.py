from django.urls import path , include
from .views import register_user, login_user, logout_user
from django.shortcuts import redirect

urlpatterns = [
    path('register/', register_user, name='register-user'),
    path('login/',login_user,name='login-user'),
    path('logout/',logout_user,name='logout-user'),
]