from django.shortcuts import render
from .models import Priority

def priority_list(request):
    priorities = Priority.objects.all()
    return render(request, 'priority_management/priority_list.html', {'priorities': priorities})
