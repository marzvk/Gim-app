from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):
    """
    Vista principal del dashboard
    """
    return render(request, "clientes/dashboard.html")
