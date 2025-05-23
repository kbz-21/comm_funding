from django.urls import path
from rest_framework_simplejwt.views import  TokenObtainPairView, TokenRefreshView

from .views import RegisterUserView, LoginView, PasswordResetRequestView, PasswordResetConfirmView
from django.contrib.auth import views as auth_views

urlpatterns = [
    # API views (class-based)
    path('register/', RegisterUserView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('reset-password/', PasswordResetRequestView.as_view(), name='reset_password'),
    path('reset-password-confirm/<str:uid>/<str:token>/', PasswordResetConfirmView.as_view(), name='reset_password_confirm'),

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # Login
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Refresh
]