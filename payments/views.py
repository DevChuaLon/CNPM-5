from django.shortcuts import render
from .models import Payment

def payment_list(request):
    payments = Payment.objects.filter(user=request.user)
    return render(request, 'payments/payment_list.html', {'payments': payments})
