from django.urls import path
from . import views

urlpatterns = [
    path('', views.schedule_list, name='schedule_list'),
    path('<int:pk>/', views.schedule_detail, name='schedule_detail'),
]
