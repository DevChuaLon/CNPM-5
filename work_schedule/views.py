from django.shortcuts import render, get_object_or_404
from .models import WorkSchedule

def schedule_list(request):
    schedules = WorkSchedule.objects.all().order_by('start_time')
    return render(request, 'work_schedule/schedule_list.html', {'schedules': schedules})

def schedule_detail(request, pk):
    schedule = get_object_or_404(WorkSchedule, pk=pk)
    return render(request, 'work_schedule/schedule_detail.html', {'schedule': schedule})
