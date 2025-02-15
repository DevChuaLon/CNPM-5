from django.contrib import admin
from .models import *

# Đăng ký các models với admin site
admin.site.register(UserProfile)
admin.site.register(Pod)
admin.site.register(PodBooking)
admin.site.register(Amenities)
admin.site.register(PodImages)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'title', 'is_read', 'created_at']
    list_filter = ['type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'pod', 'rating', 'comment', 'created_at')
    list_filter = ('rating', 'created_at', 'pod')
    search_fields = ('user__username', 'pod__pod_name', 'comment')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

