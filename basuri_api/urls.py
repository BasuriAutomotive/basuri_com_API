from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('my_admin/', include('admin_panel.urls')),
    path('accounts/', include('accounts.urls')),
    path('address/', include('address.urls')),
    path('product/', include('product.urls')),
    path('utils/', include('utils.urls')),
    path('cart/', include('cart.urls')),
    path('order/', include('order.urls')),
    path('checkout/', include('checkout.urls')),
    path('coupon/', include('discount.urls')),
    path('payment/', include('payment.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
