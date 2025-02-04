from django.urls import path
from . import views

urlpatterns = [
    path('', views.feedback_list, name='feedback_list'),
    path('create/', views.feedback_create, name='feedback_create'),
]
