from django.contrib import admin
from .models import *

# Đăng ký các models với admin site
admin.site.register(UserProfile)
admin.site.register(Pod)
admin.site.register(PodBooking)
admin.site.register(Amenities)
admin.site.register(PodImages)

# Hoặc có thể đăng ký cùng lúc như sau:
# admin.site.register((Hotel, HotelBooking, Amenities, HotelImages))

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'title', 'is_read', 'created_at']
    list_filter = ['type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']

