from django.urls import path
from . import views

urlpatterns = [
    path('', views.priority_list, name='priority_list'),
]
