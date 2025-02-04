from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.pod_list, name='pod_list'),
]
