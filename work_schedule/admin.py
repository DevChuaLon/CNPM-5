from django.contrib import admin
from .models import WorkSchedule

@admin.register(WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_time', 'end_time', 'created_at', 'updated_at')
    search_fields = ('title',)
    list_filter = ('start_time', 'end_time')
