# core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.problems_list, name='problems_list'),
    path('problems/', views.problems_list, name='problems_list'),
    path('problem/<str:short_code>/', views.problem_detail, name='problem_detail'),
    path('submissions/', views.submissions_list, name='submissions_list'),
]