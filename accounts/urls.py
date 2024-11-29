from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import *
from review.views import UserReviewListView

urlpatterns = [

    # API VIEWS IS HERE
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/profile/', UserProfileAPIView.as_view(), name="profile_api"),
    path('api/register/', RegisterView.as_view(), name="register_api"),
    path('api/login/', CustomerLoginView.as_view(), name="customer_login_api"),
    path('api/logout/', CustomerLogoutView.as_view(), name="customer_logout_api"),
    path('api/forgot_password/', ForgotPasswordView.as_view(), name="forgot_password_api"),
    path('api/reset-password/', ResetPasswordView.as_view(), name="reset_password_api"),
    path('api/change-password/', ChangePasswordView.as_view(), name="change_password_api"),
    path('api/otp-validate/', OTPValidateView.as_view(), name="otp_validate_api"),

    path('api/review/', UserReviewListView.as_view(), name="user_review_api"),

]