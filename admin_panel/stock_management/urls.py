from django.urls import path

from admin_panel.stock_management.views import ProductStockListView, ProductStockUpdateView

urlpatterns = [

    path('stock-list/', ProductStockListView.as_view(), name='product-stock-list-api'),
    path('stock-update/', ProductStockUpdateView.as_view(), name='product-stock-update-api'),

]