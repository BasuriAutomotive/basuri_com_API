from django.urls import path

from .views import *


urlpatterns = [

    # API VIEWS IS HERE
    path('api/get-country/', CountryWithStatesListAPIView.as_view(), name='get_country'),
    path('api/', UserAddressAPIView.as_view(), name="address_api"),

]