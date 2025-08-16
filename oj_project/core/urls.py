# Add these URLs to your core/urls.py

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Existing URLs
    path('', views.problems_list, name='problems_list'),
    path('problem/<str:short_code>/', views.problem_detail, name='problem_detail'),
    path('submissions/', views.submissions_list, name='submissions_list'),
    path('submit/<str:short_code>/', views.submit_solution, name='submit_solution'),
    
    # Admin URLs
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/problems/', views.admin_problems_list, name='admin_problems_list'),
    path('admin/problems/add/', views.admin_add_problem, name='admin_add_problem'),
    path('admin/problems/edit/<str:short_code>/', views.admin_edit_problem, name='admin_edit_problem'),
    path('admin/problems/delete/<str:short_code>/', views.admin_delete_problem, name='admin_delete_problem'),
    path('admin/submissions/', views.admin_submissions_list, name='admin_submissions_list'),
    
    # NEW URLs for Users and Analytics
    path('admin/users/', views.admin_users_list, name='admin_users_list'),
    path('admin/analytics/', views.admin_analytics, name='admin_analytics'),
]