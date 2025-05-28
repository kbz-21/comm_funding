from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterUserView,
    LoginView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    ProfileDetailView,
    ProfileUpdateView,
    UserUpdateView,

)

urlpatterns = [
    # API Routes
    path('api/account/register/', RegisterUserView.as_view(), name='user-register'),
    path('api/account/login/', LoginView.as_view(), name='api-login'),
    path('api/account/password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('api/account/reset-password-confirm/<str:uid>/<str:token>/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('api/account/profile/', ProfileDetailView.as_view(), name='api-profile-detail'),
    path('api/account/profile/update/', ProfileUpdateView.as_view(), name='api-profile-update'),
    path('api/account/user/update/', UserUpdateView.as_view(), name='api-user-update'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

]