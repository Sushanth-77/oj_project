# authentication/urls.py
from django.urls import path
from .views import register_user, login_user, logout_user, debug_info, test_registration

app_name = 'authentication'

urlpatterns = [
    path('register/', register_user, name='register-user'),
    path('login/', login_user, name='login-user'),
    path('logout/', logout_user, name='logout-user'),
    # Temporary debug URLs - REMOVE AFTER FIXING
    path('debug/', debug_info, name='debug'),
    path('test-reg/', test_registration, name='test-reg'),
]