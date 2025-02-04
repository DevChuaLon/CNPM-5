from django.shortcuts import render
from .models import AdditionalService

def service_list(request):
    services = AdditionalService.objects.all()
    return render(request, 'additional_services/service_list.html', {'services': services})
