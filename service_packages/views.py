from django.shortcuts import render
from .models import ServicePackage

def package_list(request):
    packages = ServicePackage.objects.all()
    return render(request, 'service_packages/package_list.html', {'packages': packages})
