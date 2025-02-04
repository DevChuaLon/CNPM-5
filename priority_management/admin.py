from django.contrib import admin
from .models import Priority

@admin.register(Priority)
class PriorityAdmin(admin.ModelAdmin):
    list_display = ('user', 'priority_level', 'created_at')
    list_filter = ('priority_level', 'created_at')
    search_fields = ('user__username',)
