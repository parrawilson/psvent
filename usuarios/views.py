from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def registro_usuario(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        if User.objects.filter(username=username).exists():
            messages.error(request, "El usuario ya existe.")
        else:
            User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, "Usuario creado correctamente.")
            return redirect('login')
    return render(request, 'usuarios/registro.html')

def login_usuario(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')  # Página principal
        else:
            messages.error(request, "Credenciales inválidas.")
    return render(request, 'usuarios/login.html')

def logout_usuario(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

@login_required
def dashboard2(request):
    return render(request, 'dashboard5.html')

