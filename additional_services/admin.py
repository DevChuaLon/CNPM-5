from django.contrib import admin
from .models import AdditionalService

@admin.register(AdditionalService)
class AdditionalServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price')
    search_fields = ('name',)
