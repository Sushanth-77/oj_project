from django.urls import path
from . import views

app_name = 'submit'

urlpatterns = [
    path("", views.submit_code, name="submit_code"),
    path("history/", views.submission_history, name="submission_history"),
]