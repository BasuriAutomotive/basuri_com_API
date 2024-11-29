from django.urls import path
from .views import *

urlpatterns = [

    # DISCOUNT APPLY URL
    # path('apply_coupon/', views.apply_coupon, name="apply_coupon"),
    
    # API URL
    path('api/apply-coupon/', ApplyCouponAPIView.as_view(), name="apply_coupon_api"),

   
]