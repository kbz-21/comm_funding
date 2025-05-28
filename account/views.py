from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import CustomUser, Profile
from .serializers import UserRegistrationSerializer, LoginSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer, CustomUserSerializer, ProfileSerializer, UserUpdateSerializer
from .forms import UserRegistrationForm, LoginForm, UserUpdateForm, ProfileUpdateForm
import logging

logger = logging.getLogger(__name__)

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

# API Views
class RegisterUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        if request.content_type.startswith('multipart'):
            form = UserRegistrationForm(request.POST, request.FILES)
            if form.is_valid():
                user = form.save()
                logger.info(f"User registered via form: {user.email}")
                tokens = get_tokens_for_user(user)
                return Response(
                    {
                        "message": "User registered successfully",
                        "user": {
                            "email": user.email,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                        },
                        "tokens": tokens
                    },
                    status=status.HTTP_201_CREATED
                )
            logger.warning(f"Form registration failed: {form.errors}")
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            serializer = UserRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                logger.info(f"User registered via API: {user.email}")
                tokens = get_tokens_for_user(user)
                return Response(
                    {
                        "message": "User registered successfully",
                        "user": {
                            "email": user.email,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                        },
                        "tokens": tokens
                    },
                    status=status.HTTP_201_CREATED
                )
            logger.warning(f"API registration failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            logger.info(f"User logged in: {user.email}")
            tokens = get_tokens_for_user(user)
            return Response(
                {
                    "message": "Login successful",
                    "user": {
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                    },
                    "tokens": tokens
                },
                status=status.HTTP_200_OK
            )
        logger.warning(f"Login failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = CustomUser.objects.get(email=email)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = PasswordResetTokenGenerator().make_token(user)
                reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
                send_mail(
                    subject="Password Reset Request",
                    message=f"Click the link to reset your password: {reset_url}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                logger.info(f"Password reset email sent to: {email}")
                return Response(
                    {"message": "Password reset link sent to your email."},
                    status=status.HTTP_200_OK
                )
            except CustomUser.DoesNotExist:
                logger.warning(f"Password reset requested for non-existent email: {email}")
                return Response(
                    {"error": "No user found with this email."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        logger.warning(f"Password reset request failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uid, token):
        data = request.data.copy()
        data['uid'] = uid
        data['token'] = token
        serializer = PasswordResetConfirmSerializer(data=data)
        if serializer.is_valid():
            uid = serializer.validated_data['uid']
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']
            try:
                user_id = force_str(urlsafe_base64_decode(uid))
                user = CustomUser.objects.get(pk=user_id)
                if PasswordResetTokenGenerator().check_token(user, token):
                    user.set_password(new_password)
                    user.save()
                    logger.info(f"Password reset successful for user: {user.email}")
                    return Response(
                        {"message": "Password reset successfully."},
                        status=status.HTTP_200_OK
                    )
                else:
                    logger.warning(f"Invalid or expired token for user: {user.email}")
                    return Response(
                        {"error": "Invalid or expired token."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except (CustomUser.DoesNotExist, ValueError):
                logger.warning(f"Invalid user ID for password reset: {uid}")
                return Response(
                    {"error": "Invalid user ID."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        logger.warning(f"Password reset confirm failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProfileDetailView(generics.RetrieveAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            return Profile.objects.get(user=self.request.user)
        except Profile.DoesNotExist:
            logger.error(f"Profile not found for user: {self.request.user.email}")
            return Response(
                {"error": "Profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

class ProfileUpdateView(generics.UpdateAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            return Profile.objects.get(user=self.request.user)
        except Profile.DoesNotExist:
            logger.error(f"Profile not found for user: {self.request.user.email}")
            return Response(
                {"error": "Profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

    def perform_update(self, serializer):
        serializer.save()
        logger.info(f"Profile updated for user: {self.request.user.email}")

class UserUpdateView(generics.UpdateAPIView):
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        serializer.save()
        logger.info(f"User updated: {self.request.user.email}")
