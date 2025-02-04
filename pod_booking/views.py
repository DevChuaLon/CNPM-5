from django.shortcuts import render
from .models import Pod

def pod_list(request):
    pods = Pod.objects.filter(is_available=True)
    return render(request, 'pod_booking/pod_list.html', {'pods': pods})
