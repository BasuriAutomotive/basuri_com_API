import os
import random
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.contrib.auth import login, authenticate, logout
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated

from accounts.models import Account, Profile

class RegisterView(APIView):
    authentication_classes = []
    permission_classes = []
    
    def post(self, request, *args, **kwargs):
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        email = request.data.get('email')
        phone_number = request.data.get('phone_number')
        password = request.data.get('password')

        if Account.objects.filter(email=email).exists():
            return Response({'detail': 'Account already exists. Please log in.'}, status=status.HTTP_400_BAD_REQUEST)

        user = Account.objects.create_user(email=email, password=password, phone_number=phone_number)
        user.is_active = False
        user.is_customer = True
        user.save()

        otp = str(random.randint(1000, 9999))
        profile = Profile(user=user, first_name=first_name, last_name=last_name, otp=otp)
        profile.user_id = user.id
        profile.save()

        self.send_otp(otp, user)

        return Response({'detail': 'Account created successfully. Check your email for OTP.'}, status=status.HTTP_201_CREATED)

    def send_otp(self, otp, user):
        subject = 'Password Reset OTP Code'
        message = f'Your OTP for login is: {otp}'
        from_email = 'info@basuriautomotive.com'  # SYSTEM SENDER EMAIL
        recipient_list = [user.email]
        send_mail(subject, message, from_email, recipient_list)

class OTPValidateView(APIView):

    authentication_classes = []
    permission_classes = []
    
    def post(self, request, *args, **kwargs):
        otp = request.data.get('otp')
        email = request.data.get('email')

        if Account.objects.filter(email=email).exists():
            current_user = Account.objects.get(email=email)
            profile = Profile.objects.get(user=current_user)

            if profile.otp == otp:
                current_user.is_active = True
                current_user.save()
                login(request, current_user, backend='django.contrib.auth.backends.ModelBackend')
                return Response({'detail': 'OTP is Verified!'}, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'Please Enter Valid OTP'}, status=status.HTTP_400_BAD_REQUEST)
            
class CustomerLoginView(APIView):
    
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')

        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email=email)
            if user.is_active:
                authenticated_user = authenticate(email=email, password=password)
                if authenticated_user:
                    # if user.role=="customer" or user.role=="staff":
                    login(request, authenticated_user)
                    refresh = RefreshToken.for_user(authenticated_user)
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
                return Response({'detail': 'User must be active!'}, status=status.HTTP_400_BAD_REQUEST)
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
        if Account.objects.filter(email=email).exists():
            current_user = Account.objects.get(email=email)

            otp = str(random.randint(100000, 999999))

            profile = Profile.objects.get(user=current_user)
            profile.otp = otp
            profile.save()

            self.send_otp(otp, current_user)

            return Response({'detail': 'OTP Sent on Your Email!'}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Account does not exist!'}, status=status.HTTP_400_BAD_REQUEST)

    def send_otp(self, otp, user):
        subject = 'Password Reset OTP Code'
        message = f'Your OTP for login is: {otp}'
        from_email = 'info@basuriautomotive.com'  # SYSTEM SENDER EMAIL
        recipient_list = [user.email]
        send_mail(subject, message, from_email, recipient_list)

class OTPValidateView(APIView):

    authentication_classes = []
    permission_classes = []
    
    def post(self, request, *args, **kwargs):
        otp = request.data.get('otp')
        email = request.data.get('email')

        if Account.objects.filter(email=email).exists():
            current_user = Account.objects.get(email=email)
            profile = Profile.objects.get(user=current_user)
            server_otp = profile.otp

            if server_otp == otp:
                current_user.is_active = True
                current_user.save()
                login(request, current_user, backend='django.contrib.auth.backends.ModelBackend')
                return Response({'detail': 'OTP is Verified!'}, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'Please Enter Valid OTP'}, status=status.HTTP_400_BAD_REQUEST)

class OTPValidateForgotPasswordView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        otp = request.data.get('otp')
        email = request.session.get('email')

        if Account.objects.filter(email=email).exists():
            current_user = Account.objects.get(email=email)
            profile = Profile.objects.get(user=current_user)
            server_otp = profile.otp

            if server_otp == otp:
                return Response({'detail': 'OTP is Verified!'}, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'Please Enter Valid OTP'}, status=status.HTTP_400_BAD_REQUEST)

# RESET PASSWORD API VIEW
class ResetPasswordView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        
        otp = request.data.get('otp')
        email = request.data.get('email')
        password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')

        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email=email)
            profile = Profile.objects.get(user=user)
            server_otp = profile.otp
            server_otp = int(server_otp)
            otp = int(otp)

            if server_otp == otp:
                if password == confirm_password:
                    user.set_password(password)
                    user.save()
                    return Response({'detail': 'Password reset successful'}, status=status.HTTP_200_OK)
                else:
                    return Response({'detail': 'Password do not match!'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'detail': 'Please Enter Valid OTP'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'detail': 'Invalid values'}, status=status.HTTP_401_UNAUTHORIZED)
        
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
        # Get the authenticated user
        user = request.user
        
        # Get the profile associated with the user
        profile = get_object_or_404(Profile, user=user)
        
        # Prepare the response data in the desired format
        data = {
            "img": profile.image,
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "contact_no": user.phone_number,
            "email_address": user.email
        }
        
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        data = request.data
        profile = get_object_or_404(Profile, user=user)

        try:
            # Update first and last name
            profile.first_name = data.get('first_name', profile.first_name)
            profile.last_name = data.get('last_name', profile.last_name)

            # Handle profile picture upload
            if 'img' in request.FILES:
                # Save the image to a specific folder within MEDIA_ROOT (e.g., 'images')
                img = request.FILES['img']
                img_name = f"profile_images/{user.id}_{img.name}"  # Customize the name to avoid conflicts
                img_path = os.path.join(settings.MEDIA_ROOT, img_name)

                # Save the file to the media folder
                with default_storage.open(img_path, 'wb+') as destination:
                    for chunk in img.chunks():
                        destination.write(chunk)

                # Generate the URL for the saved image
                img_url = request.build_absolute_uri(settings.MEDIA_URL + img_name)

                # Update image field with the image URL
                profile.image = img_url

            profile.save()

            response_data = {
                "img": profile.image,  # Return the URL
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "email_address": user.email,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response({"error": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)