# oj_project/core/urls.py
from django.urls import path
from django.shortcuts import redirect
from .views import (
    register_user, login_user, logout_user, 
    problems_list, problem_detail, submissions_list,ai_review_submission
)

app_name = 'core'

# Root redirect function
def home_redirect(request):
    return redirect('/auth/register/')

urlpatterns = [
    # Root redirect
    path('', home_redirect, name='home'),
    
    # Authentication URLs with auth/ prefix
    path('auth/register/', register_user, name='register-user'),
    path('auth/login/', login_user, name='login-user'),
    path('auth/logout/', logout_user, name='logout-user'),
    
    # Main application URLs
    path('problems/', problems_list, name='problems_list'),
    path('problem/<str:short_code>/', problem_detail, name='problem_detail'),
    path('ai-review/<int:submission_id>/', ai_review_submission, name='ai_review_submission'),
    path('submissions/', submissions_list, name='submissions_list'),
]