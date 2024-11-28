from django.urls import path

from admin_panel.customer.views import CustomerListView

urlpatterns = [

    path('customer-list/', CustomerListView.as_view(), name='customer-list-api'),

]