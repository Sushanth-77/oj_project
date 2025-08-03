# core/urls.py - Updated with separated apps
from django.urls import path
from django.shortcuts import redirect
from .views import problems_list, problem_detail, submissions_list

app_name = 'core'

# Root redirect function
def home_redirect(request):
    return redirect('/auth/register/')

urlpatterns = [
    # Root redirect
    path('', home_redirect, name='home'),
    
    # Main application URLs
    path('problems/', problems_list, name='problems_list'),
    path('problem/<str:short_code>/', problem_detail, name='problem_detail'),
    path('submissions/', submissions_list, name='submissions_list'),
]