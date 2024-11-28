from django.urls import path

from .views import *


urlpatterns = [

    path('api/order-list/', OrderListView.as_view(), name='order-list-api'),
    path('api/order-details/<int:order_id>/', OrderDetailView.as_view(), name='order-detail-api'),
    path('api/order-tracking/', OrderTrackingAPIView.as_view(), name='order-tracking-api'),
    path('api/invoice/<int:order_id>/', DownloadInvoicePDFView.as_view(), name='download-invoice-api'),

]