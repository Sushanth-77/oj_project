# authentication/urls.py
from django.urls import path
from .views import register_user, login_user, logout_user, run_migrations_now

app_name = 'authentication'

urlpatterns = [
    path('register/', register_user, name='register-user'),
    path('login/', login_user, name='login-user'),
    path('logout/', logout_user, name='logout-user'),
    path('migrate-now/', run_migrations_now, name='migrate-now'),  # TEMPORARY
]