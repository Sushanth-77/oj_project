# oj_project/core/urls.py
from django.urls import path
from django.shortcuts import redirect
from .views import (
    register_user, login_user, logout_user, 
    problems_list, problem_detail, submissions_list
)

app_name = 'core'

urlpatterns = [
    # Authentication URLs (will be available at /auth/)
    path('register/', register_user, name='register-user'),
    path('login/', login_user, name='login-user'),
    path('logout/', logout_user, name='logout-user'),
    
    # Main application URLs (will be available at root level)
    path('problems/', problems_list, name='problems_list'),
    path('problem/<str:short_code>/', problem_detail, name='problem_detail'),
    path('submissions/', submissions_list, name='submissions_list'),
]