from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render


def home(request):
    return render(request, 'home.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')), 
    path('additional_services/', include('additional_services.urls')),
    path('feedback/', include('feedback.urls')),
    path('notifications/', include('notifications.urls')),
    path('payments/', include('payments.urls')),
    path('pod_booking/', include('pod_booking.urls')),
    path('priority_management/', include('priority_management.urls')),
    path('service_packages/', include('service_packages.urls')),
    path('users/', include('users.urls')),
    path('work_schedule/', include('work_schedule.urls')),
    path('', home, name='home'), 
]