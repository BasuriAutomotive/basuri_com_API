from django.urls import path

from admin_panel.product.views import ProductListView

urlpatterns = [

    path('product-list/', ProductListView.as_view(), name='product-list-api'),

]