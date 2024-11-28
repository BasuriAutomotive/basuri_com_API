from django.urls import path

from admin_panel.order.views import OrderListView, DownloadInvoicePDFView

urlpatterns = [

    path('order-list/', OrderListView.as_view(), name='order-list-api'),
    path('invoice/<int:order_id>/', DownloadInvoicePDFView.as_view(), name='download-invoice-api-admin'),

]