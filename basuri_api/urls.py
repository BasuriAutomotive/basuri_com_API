from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static


urlpatterns = [
    path('apiserver/admin/', admin.site.urls),
    path('apiserver/my_admin/', include('admin_panel.urls')),
    path('apiserver/accounts/', include('accounts.urls')),
    path('apiserver/address/', include('address.urls')),
    path('apiserver/products/', include('product.urls')),
    path('apiserver/utils/', include('utils.urls')),
    path('apiserver/cart/', include('cart.urls')),
    path('apiserver/order/', include('order.urls')),
    path('apiserver/checkout/', include('checkout.urls')),
    path('apiserver/coupon/', include('discount.urls')),
    path('apiserver/payment/', include('payment.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
