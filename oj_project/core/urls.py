# oj_project/core/urls.py
from django.urls import path
from django.shortcuts import redirect
from .views import (
    register_user, login_user, logout_user, 
    problems_list, problem_detail, submissions_list
)

app_name = 'core'

urlpatterns = [
    path('', lambda request: redirect('/problems/', permanent=False)),
    path('register/', register_user, name='register-user'),
    path('login/', login_user, name='login-user'),
    path('logout/', logout_user, name='logout-user'),
    path('problems/', problems_list, name='problems_list'),
    path('problem/<str:short_code>/', problem_detail, name='problem_detail'),  # Fixed path
    path('submissions/', submissions_list, name='submissions_list'),
]