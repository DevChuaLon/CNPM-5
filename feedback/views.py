from django.shortcuts import render, redirect
from .models import Feedback
from .forms import FeedbackForm

def feedback_list(request):
    feedbacks = Feedback.objects.all()
    return render(request, 'feedback/feedback_list.html', {'feedbacks': feedbacks})

def feedback_create(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()
            return redirect('feedback_list')
    else:
        form = FeedbackForm()
    return render(request, 'feedback/feedback_create.html', {'form': form})
