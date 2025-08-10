# compiler/urls.py
from django.urls import path
from .views import ai_review_submission

app_name = 'compiler'

urlpatterns = [
    path('ai-review/<int:submission_id>/', ai_review_submission, name='ai_review_submission'),
]