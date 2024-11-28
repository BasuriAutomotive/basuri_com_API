from django.urls import path

from .views import *


urlpatterns = [

    path('api/add-to-cart/', AddToCartAPIView.as_view(), name='add_to_cart_api'),
    path('api/view-cart/', ViewCartAPIView.as_view(), name='view_cart_api'),
    path('api/add-to-cart-non-auth/', AddToCartNonAuthenticatedAPIView.as_view(), name='add_to_cart_non_auth_api'),
    path('api/view-cart-non-auth/', ViewCartNonAuthenticatedAPIView.as_view(), name='view_cart_non_auth_api'),
    path('api/decrease-cart-item/', DecreaseCartItemAPIView.as_view()),
    path('api/decrease-cart-item-non-auth/<str:cart_id>/', DecreaseCartItemNonAuthenticatedAPIView.as_view()),
    path('api/remove-cart-items/', RemoveAllCartItemsAPIView.as_view()),
    path('api/remove-cart-items-non-auth/<str:cart_id>/', RemoveAllCartItemsNonAuthenticatedAPIView.as_view()),

]