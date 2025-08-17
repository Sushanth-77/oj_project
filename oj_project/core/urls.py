# core/urls.py - Updated with async submission status endpoint
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Main pages
    path('', views.problems_list, name='problems_list'),
    path('problem/<str:short_code>/', views.problem_detail, name='problem_detail'),
    path('submissions/', views.submissions_list, name='submissions_list'),
    path('submit/<str:short_code>/', views.submit_solution, name='submit_solution'),
    
    # AJAX endpoint for checking submission status
    path('submission/<int:submission_id>/status/', views.submission_status, name='submission_status'),
    
    # Admin pages
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/problems/', views.admin_problems_list, name='admin_problems_list'),
    path('admin/problems/add/', views.admin_add_problem, name='admin_add_problem'),
    path('admin/problems/<str:short_code>/edit/', views.admin_edit_problem, name='admin_edit_problem'),
    path('admin/problems/<str:short_code>/delete/', views.admin_delete_problem, name='admin_delete_problem'),
    path('admin/submissions/', views.admin_submissions_list, name='admin_submissions_list'),
    path('admin/submissions/<int:submission_id>/', views.admin_submission_detail, name='admin_submission_detail'),
    path('admin/users/', views.admin_users_list, name='admin_users_list'),
    path('admin/analytics/', views.admin_analytics, name='admin_analytics'),
]