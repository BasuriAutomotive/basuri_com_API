from django.urls import path

from .views import *


urlpatterns = [

    # API VIEWS IS HERE
    path('api/menuitems/', MenuItemListCreateView.as_view(), name='menuitem-list-create'),

]