# core/urls.py
from django.urls import path
from .views import problems_list, problem_detail, submissions_list

app_name = 'core'

urlpatterns = [
    # Remove the empty path redirect since it's handled in main urls.py
    path('', problems_list, name='problems_list'),  # This handles /problems/
    path('<str:short_code>/', problem_detail, name='problem_detail'),  # This handles /problems/<code>/
    path('submissions/', submissions_list, name='submissions_list'),  # This handles /problems/submissions/
]