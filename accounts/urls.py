from django.urls import path
from .views import register_view, login_view, verify_email_view, profile_view, forgot_password_view, reset_password_view, delete_account_view

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('verify-email/', verify_email_view, name='verify_email'),
    path('profile/', profile_view, name='profile'),
    path('olvido/', forgot_password_view, name='forgot_password'),
    path('restablecer/', reset_password_view, name='reset_password'),
    path('borrar-cuenta/', delete_account_view, name='delete_account'),
]