from django.shortcuts import render

# Create your views here.
# accounts/views.py
from django.contrib.auth import authenticate, login
from django.http import JsonResponse

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Credenciales inválidas'})
    return JsonResponse({'status': 'error', 'message': 'Solicitud no válida'})


def login_page(request):
    return render(request, 'accounts/login.html')