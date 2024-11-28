from django.urls import include, path

urlpatterns = [
    
    path('order/', include('admin_panel.order.urls')),
    path('customer/', include('admin_panel.customer.urls')),
    path('product/', include('admin_panel.product.urls')),
    path('stock_management/', include('admin_panel.stock_management.urls')),

]