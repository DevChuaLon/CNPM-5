from django.urls import path
from . import views

urlpatterns = [
    path('', views.package_list, name='service_package_list'),
]
