from django.urls import path

from payment.views import *
from .views import *


urlpatterns = [
    
    # Paypal Urls
    path('api/paypal/execute/', ExecutePayPalPaymentAPIView.as_view(), name='paypal-execute'),
    path('api/paypal/cancel/', CancelPayPalPaymentAPIView.as_view(), name='paypal-cancel'),
    path('api/paypal/retry/', RetryExistingPayPalPaymentAPIView.as_view(), name='paypal-retry'),
    path('api/finalize-order/', FinalizeOrderAfterPaymentAPIView.as_view(), name='finalize-order'),

    # Stripe Urls
    path('api/create-intent/', create_payment_intent, name='create_payment_intent'),
  
]