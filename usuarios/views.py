# usuarios/views.py
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import PerfilUsuario
from .forms import RegistroUsuarioForm, PerfilUsuarioForm,UserEditForm
from django.db import IntegrityError, transaction

@login_required
@login_required
def registro_usuario(request):
    if request.method == 'POST':
        form_usuario = RegistroUsuarioForm(request.POST)
        form_perfil = PerfilUsuarioForm(request.POST, request.FILES)
        
        if form_usuario.is_valid() and form_perfil.is_valid():
            try:
                with transaction.atomic():
                    # 1. Crear usuario
                    user = form_usuario.save()
                    
                    # 2. Obtener el perfil creado por la señal
                    perfil = user.perfil
                    
                    # 3. Actualizar campos normales
                    perfil.cedula = form_perfil.cleaned_data['cedula'] or None
                    perfil.telefono = form_perfil.cleaned_data['telefono']
                    perfil.direccion = form_perfil.cleaned_data['direccion']
                    perfil.tipo_usuario = form_perfil.cleaned_data['tipo_usuario']
                    perfil.fecha_nacimiento = form_perfil.cleaned_data['fecha_nacimiento']
                    perfil.foto_perfil = form_perfil.cleaned_data['foto_perfil']
                    perfil.es_vendedor = form_perfil.cleaned_data['es_vendedor']
                    perfil.es_cobrador = form_perfil.cleaned_data['es_cobrador']
                    perfil.empresa = form_perfil.cleaned_data['empresa']
                    perfil.tipo_doc = form_perfil.cleaned_data['tipo_doc']
                    
                    # Guardar primero el perfil para tener un ID
                    perfil.save()
                    
                    # 4. Manejar el campo ManyToMany (sucursales) correctamente
                    if form_perfil.cleaned_data['sucursales']:
                        perfil.sucursales.set(form_perfil.cleaned_data['sucursales'])
                    
                messages.success(request, "Usuario creado correctamente.")
                return redirect('lista_usuarios')
                
            except IntegrityError as e:
                if User.objects.filter(username=form_usuario.cleaned_data.get('username')).exists():
                    user.delete()
                messages.error(request, f"Error al crear el usuario: {str(e)}")
                return redirect('registro')
    else:
        form_usuario = RegistroUsuarioForm()
        form_perfil = PerfilUsuarioForm()

    return render(request, 'usuarios/registro.html', {
        'form_usuario': form_usuario,
        'form_perfil': form_perfil,
    })



@login_required
def editar_usuario(request, usuario_id):
    usuario = get_object_or_404(User, pk=usuario_id)
    perfil = usuario.perfil

    if request.method == 'POST':
        form_usuario = UserEditForm(request.POST, instance=usuario)
        form_perfil = PerfilUsuarioForm(request.POST, request.FILES, instance=perfil)

        if form_usuario.is_valid() and form_perfil.is_valid():
            try:
                with transaction.atomic():
                    # Guardar el formulario de usuario
                    user = form_usuario.save()
                    
                    # Guardar el formulario de perfil sin commit para manejar manualmente
                    perfil = form_perfil.save(commit=False)
                    
                    # Actualizar campos específicos si es necesario
                    perfil.usuario = user
                    perfil.save()
                    
                    # Guardar relaciones many-to-many (sucursales)
                    form_perfil.save_m2m()
                    
                    messages.success(request, "Usuario actualizado correctamente.")
                    return redirect('lista_usuarios')
                    
            except Exception as e:
                messages.error(request, f"Error al actualizar el usuario: {str(e)}")
                return redirect('editar_usuario', usuario_id=usuario.id)
    else:
        form_usuario = UserEditForm(instance=usuario)
        form_perfil = PerfilUsuarioForm(instance=perfil)

    return render(request, 'usuarios/editar_usuario.html', {
        'form_usuario': form_usuario,
        'form_perfil': form_perfil,
        'usuario': usuario,
        'modo': 'editar',
        'titulo': f'Editar Usuario: {usuario.username}'
    })


@login_required
def perfil_usuario(request):
    # Asegurarse que el usuario tenga perfil
    if not hasattr(request.user, 'perfil'):
        PerfilUsuario.objects.create(usuario=request.user)
    
    if request.method == 'POST':
        form_usuario = UserEditForm(request.POST, instance=request.user)
        form_perfil = PerfilUsuarioForm(request.POST, request.FILES, instance=request.user.perfil)
        
        if form_usuario.is_valid() and form_perfil.is_valid():
            form_usuario.save()
            form_perfil.save()
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect('perfil')
    else:
        form_usuario = UserEditForm(instance=request.user)
        form_perfil = PerfilUsuarioForm(instance=request.user.perfil)
    
    return render(request, 'usuarios/perfil.html', {
        'form_usuario': form_usuario,
        'form_perfil': form_perfil
    })



def login_usuario(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Verificar y crear perfil si no existe
            if not hasattr(user, 'perfil'):
                PerfilUsuario.objects.create(usuario=user)
                
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Credenciales inválidas.")
    return render(request, 'usuarios/login.html')




def lista_usuarios(request):
    usuario = PerfilUsuario.objects.all()
    return render(request, 'usuarios/lista.html', {'usuarios': usuario})
# (Mantener las demás vistas como logout_usuario y dashboard)

def logout_usuario(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

@login_required
def dashboard2(request):
    return render(request, 'dashboard5.html')



