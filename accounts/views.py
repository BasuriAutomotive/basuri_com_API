import os
from datetime import datetime, timedelta
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import authenticate, logout
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from accounts.models import Account, Profile
from utils.views import send_otp, validate_otp, resend_otp

current_url = settings.CURRENT_URL

class RegisterView(APIView):
    authentication_classes = []
    permission_classes = []
    def post(self, request, *args, **kwargs):
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        email = request.data.get('email')
        email = email.lower()
        phone_number = request.data.get('phone_number')
        password = request.data.get('password')
        if Account.objects.filter(email=email).exists():
            return Response({'detail': 'Account already exists. Please log in.'}, status=status.HTTP_400_BAD_REQUEST)
        user = Account.objects.create_user(email=email, password=password, phone_number=phone_number)
        user.is_active = False
        user.is_customer = True
        user.save()
        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'image': f"{current_url}media/profile_images/default.png",
                'country': ""
            }
        )
        subject = "Verify Your Email - Basuri Automotive"
        headline = "Register OTP"
        email=user.email
        valid_till = send_otp(email, headline, subject)
        return Response({'detail': 'Account created successfully. Check your email for OTP.', 'valid_till': valid_till}, status=status.HTTP_201_CREATED)
    
            
class CustomerLoginView(APIView):
    authentication_classes = []
    permission_classes = []
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        email = email.lower()
        password = request.data.get('password')
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email=email)
            if user.is_active:
                authenticated_user = authenticate(email=email, password=password)
                if authenticated_user:
                    # if user.role=="customer" or user.role=="staff":
                    refresh = RefreshToken.for_user(user)
                    return Response({
                        'access': str(refresh.access_token),
                        'refresh': str(refresh),
                        'role' : user.role
                    })
                    # else:
                    #     return Response({'detail': 'Customer access not allowed!'}, status=status.HTTP_403_FORBIDDEN)
                else:
                    return Response({'detail': 'Wrong Password!'}, status=status.HTTP_401_UNAUTHORIZED)
            else:
                subject = "Verify Your Email - Basuri Automotive"
                headline = "Account Activate OTP"
                email=user.email
                valid_till = send_otp(email, headline, subject)
                return Response({
                    'detail': 'User is inactive. Please validate OTP to activate your account.',
                    'redirect_to_otp_page': True,
                    'valid_till' : valid_till
                }, status=status.HTTP_401_UNAUTHORIZED)
                # return Response({'detail': 'User must be active!'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'detail': 'User Not registered!'}, status=status.HTTP_400_BAD_REQUEST)
        

class CustomerLogoutView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        logout(request)
        return Response({'detail': 'You are logged out.'}, status=status.HTTP_200_OK)
    

class ForgotPasswordView(APIView):
    authentication_classes = []
    permission_classes = []
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        email = email.lower()
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email=email)
            email=user.email
            subject = "Reset Your Password - Basuri Automotive"
            headline = "Reset Password OTP"
            valid_till = send_otp(email, headline, subject)
            return Response({'detail': 'OTP Sent on Your Email!', 'valid_till': valid_till}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Account does not exist!'}, status=status.HTTP_400_BAD_REQUEST)


class OTPValidateView(APIView):
    authentication_classes = []  
    permission_classes = []  
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        email = email.lower()
        otp_code = request.data.get('otp')
        try:
            user = Account.objects.get(email=email)
        except Account.DoesNotExist:
            return Response({'detail': 'User does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        is_valid, message = validate_otp(user, otp_code)
        if is_valid:
            user.is_active = True
            user.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'detail': 'OTP is verified.',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'role' : user.role
            }, status=status.HTTP_200_OK)
        else:
            return Response({'detail': message}, status=status.HTTP_400_BAD_REQUEST)
        

class ResetPasswordView(APIView):
    authentication_classes = []
    permission_classes = []
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        email = email.lower()
        otp_code = request.data.get('otp')
        password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')
        try:
            user = Account.objects.get(email=email)
        except Account.DoesNotExist:
            return Response({'detail': 'User does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        is_valid, message = validate_otp(user, otp_code)
        if is_valid:
            if password != confirm_password:
                return Response({'detail': 'Passwords do not match!'}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(password)
            user.save()
            return Response({'detail': "Password reset was successful. Please proceed to log in."}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': message}, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        data = request.data
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        if not user.check_password(old_password):
            return Response({'detail': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)
        if len(new_password) < 6:
            return Response({'detail': 'New password must be at least 6 characters long'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        return Response({'detail': 'Password changed successfully'}, status=status.HTTP_200_OK)


class UserProfileAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        profile = get_object_or_404(Profile, user=user)
        data = {
            "img": profile.image,
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "contact_no": user.phone_number,
            "email_address": user.email,
            "role" : user.role
        }
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        data = request.data
        profile = get_object_or_404(Profile, user=user)
        try:
            profile.first_name = data.get('first_name', profile.first_name)
            profile.last_name = data.get('last_name', profile.last_name)
            if 'img' in request.FILES:
                img = request.FILES['img']
                img_name = f"profile_images/{user.id}_{img.name}"
                img_path = os.path.join(settings.MEDIA_ROOT, img_name)
                with default_storage.open(img_path, 'wb+') as destination:
                    for chunk in img.chunks():
                        destination.write(chunk)
                img_url = request.build_absolute_uri(settings.MEDIA_URL + img_name)
                profile.image = img_url
            profile.save()
            response_data = {
                "img": profile.image,
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "email_address": user.email,
            }
            return Response(response_data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({"error": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class ResendOTPAPIView(APIView):
    authentication_classes = []
    permission_classes = []
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        email = email.lower()
        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
        email = email.lower()
        try:
            validate_email(email)
        except ValidationError:
            return Response({'error': 'Invalid email format.'}, status=status.HTTP_400_BAD_REQUEST)
        try : 
            user = Account.objects.get(email=email)
        except:
            return Response({"detail": "User does not exist!"}, status=status.HTTP_400_BAD_REQUEST)

        subject = "Verify OTP - Basuri Automotive"
        headline = "Login OTP"

        try:
            otp = resend_otp(user.email, headline, subject )
            valid_till = datetime.now() + timedelta(minutes=3)
            return Response({
                "message": "OTP has been resent to your email.",
                "valid_till" : valid_till,
                "otp_expiry": otp.expires_at
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "message": "Failed to resend OTP. Please try again.",
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        

class SignInView(APIView):
    authentication_classes = []
    permission_classes = []
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
        email = email.lower()
        try:
            validate_email(email)
        except ValidationError:
            return Response({'error': 'Invalid email format.'}, status=status.HTTP_400_BAD_REQUEST)

        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email=email)
            subject = "Verify OTP - Basuri Automotive"
            headline = "Login OTP"
            email=user.email
            valid_till = send_otp(email, headline, subject)
            return Response({
                'detail': 'Check email for login code.',
                'valid_till' : valid_till
            }, status=status.HTTP_200_OK)
        else:
            user = Account.objects.create_user(email=email)
            user.is_active = False
            user.is_customer = True
            user.save()
            profile, created = Profile.objects.get_or_create(
                user=user,
                defaults={
                    'first_name': "",
                    'last_name': "",
                    'image': f"{current_url}media/profile_images/default.png",
                    'country': ""
                }
            )
            subject = "Verify OTP - Basuri Automotive"
            headline = "Login OTP"
            email=user.email
            valid_till = send_otp(email, headline, subject)
        return Response({
            'detail': 'Check email for login code.',
            'valid_till': valid_till
        }, status=status.HTTP_201_CREATED)