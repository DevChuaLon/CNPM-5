from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username',)
