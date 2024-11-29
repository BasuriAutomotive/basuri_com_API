from django.urls import path

from .views import *

urlpatterns = [

    path('api/', CheckoutAPIView.as_view(), name='checkout-api'),
    path('api/guest/', GuestCheckoutAPIView.as_view(), name='guest-checkout-api'),
    
]