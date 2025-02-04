from django.contrib import admin
from .models import Pod

@admin.register(Pod)
class PodAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity', 'is_available')
    list_filter = ('is_available',)
