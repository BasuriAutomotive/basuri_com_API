from django.urls import path

from .views import *


urlpatterns = [

    # API VIEWS IS HERE
    path('api/products/', ProductListView.as_view(), name='api_shop'),
    path('api/product/<slug:slug>/', ProductDetailsView.as_view(), name='api_product_details'),
    path('api/category/<slug:slug>/', CategoryView.as_view(), name='api_category_details'),
    path('api/search/', ProductSearchAPIView.as_view(), name='product-search'),

]