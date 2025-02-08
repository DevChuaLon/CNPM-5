"""pod URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . views import *
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from podProject import settings
from django.conf.urls.static import static
from . import views


urlpatterns = [
    path('', index, name='index'),
    path('signin/', signin, name='signin'),
    path('signup/', signup, name='signup'),
    path('signout/', signout, name='signout'),
    path('pod/<uid>/', get_pod, name='get_pod'),
    path('profile/', user_profile, name='user_profile'),
    path('bookings/', booking_history, name='booking_history'),
    path('booking/cancel/<uuid:booking_id>/', cancel_booking, name='cancel_booking'),
    path('profile/edit/', edit_profile, name='edit_profile'),
    path('notifications/', get_notifications, name='get_notifications'),
    path('notifications/mark-read/<int:notification_id>/', 
         mark_notification_as_read, name='mark_notification_as_read'),
    path('notifications/mark-all-read/', 
         views.mark_all_notifications_as_read, 
         name='mark_all_notifications_as_read'),
    path('pod/<str:pod_id>/feedback/', views.add_feedback, name='add_feedback'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
    
urlpatterns += staticfiles_urlpatterns()