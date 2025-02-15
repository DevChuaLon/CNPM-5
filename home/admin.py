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

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'payment_method', 'status', 'transaction_id', 'created_at', 'pod', 'description')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('user__username', 'transaction_id', 'description')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('user', 'pod', 'amount', 'description')
        }),
        ('Chi tiết thanh toán', {
            'fields': ('payment_method', 'transaction_id', 'status')
        }),
        ('Thông tin thời gian', {
            'fields': ('created_at', 'updated_at')
        })
    )

    def get_readonly_fields(self, request, obj=None):
        if obj: # Editing an existing object
            return self.readonly_fields + ('user', 'pod', 'amount', 'transaction_id')
        return self.readonly_fields

    def has_add_permission(self, request):
        return False # Không cho phép thêm payment trực tiếp từ admin

    def has_delete_permission(self, request, obj=None):
        return False # Không cho phép xóa payment

