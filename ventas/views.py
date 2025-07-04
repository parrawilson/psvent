from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.forms import inlineformset_factory
from .models import Venta, DetalleVenta, Cliente
from .forms import VentaForm, DetalleVentaForm, ClienteForm, FinalizarVentaForm
from usuarios.models import PerfilUsuario
from almacen.models import Stock

@login_required
def lista_ventas(request):
    ventas = Venta.objects.select_related(
        'cliente', 'vendedor', 'vendedor__usuario', 'caja'
    ).order_by('-fecha')
    
    return render(request, 'ventas/lista_ventas.html', {
        'ventas': ventas,
        'titulo': 'Lista de Ventas'
    })

@login_required
def crear_venta(request):
    DetalleFormSet = inlineformset_factory(
        Venta, 
        DetalleVenta, 
        form=DetalleVentaForm,
        extra=1,
        can_delete=True
    )
    
    if request.method == 'POST':
        form = VentaForm(request.POST)
        formset = DetalleFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                # Crear la venta
                venta = form.save(commit=False)
                venta.vendedor = request.user.perfil
                
                # Generar número de venta
                from datetime import datetime
                venta.numero = f"V-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                
                venta.save()
                
                # Guardar los detalles
                detalles = formset.save(commit=False)
                for detalle in detalles:
                    detalle.venta = venta
                    detalle.save()
                
                # Calcular totales
                venta.calcular_totales()
                
                messages.success(request, 'Venta creada correctamente')
                return redirect('ventas:editar_venta', venta_id=venta.id)
    else:
        form = VentaForm()
        formset = DetalleFormSet()
    
    return render(request, 'ventas/formulario_venta.html', {
        'form': form,
        'formset': formset,
        'titulo': 'Nueva Venta'
    })

@login_required
def editar_venta(request, venta_id):
    venta = get_object_or_404(Venta, pk=venta_id)
    
    # Solo permitir edición si está en estado BORRADOR
    if venta.estado != 'BORRADOR':
        messages.error(request, 'Solo se pueden editar ventas en estado Borrador')
        return redirect('ventas:lista_ventas')
    
    DetalleFormSet = inlineformset_factory(
        Venta, 
        DetalleVenta, 
        form=DetalleVentaForm,
        extra=1,
        can_delete=True
    )
    
    if request.method == 'POST':
        form = VentaForm(request.POST, instance=venta)
        formset = DetalleFormSet(request.POST, instance=venta)
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()
                venta.calcular_totales()
                
                messages.success(request, 'Venta actualizada correctamente')
                return redirect('ventas:lista_ventas')
    else:
        form = VentaForm(instance=venta)
        formset = DetalleFormSet(instance=venta)
    
    return render(request, 'ventas/formulario_venta.html', {
        'form': form,
        'formset': formset,
        'venta': venta,
        'titulo': f'Editar Venta: {venta.numero}'
    })

@login_required
def finalizar_venta(request, venta_id):
    venta = get_object_or_404(Venta, pk=venta_id)
    
    if venta.estado != 'BORRADOR':
        messages.error(request, 'Solo se pueden finalizar ventas en estado Borrador')
        return redirect('ventas:lista_ventas')
    
    if request.method == 'POST':
        form = FinalizarVentaForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    venta.finalizar(
                        caja=form.cleaned_data['caja'],
                        tipo_pago=form.cleaned_data['tipo_pago']
                    )
                    messages.success(request, 'Venta finalizada correctamente')
                    return redirect('ventas:detalle_venta', venta_id=venta.id)
            except Exception as e:
                messages.error(request, f'Error al finalizar venta: {str(e)}')
                return redirect('ventas:finalizar_venta', venta_id=venta.id)
    else:
        form = FinalizarVentaForm()
    
    return render(request, 'ventas/finalizar_venta.html', {
        'venta': venta,
        'form': form,
        'titulo': f'Finalizar Venta: {venta.numero}'
    })

@login_required
def detalle_venta(request, venta_id):
    venta = get_object_or_404(Venta, pk=venta_id)
    return render(request, 'ventas/detalle_venta.html', {
        'venta': venta,
        'titulo': f'Detalle de Venta: {venta.numero}'
    })

# CRUD para Clientes
@login_required
def lista_clientes(request):
    clientes = Cliente.objects.all().order_by('nombre_completo')
    return render(request, 'ventas/lista_clientes.html', {
        'clientes': clientes,
        'titulo': 'Lista de Clientes'
    })

@login_required
def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente creado correctamente')
            return redirect('ventas:lista_clientes')
    else:
        form = ClienteForm()
    
    return render(request, 'ventas/formulario_cliente.html', {
        'form': form,
        'titulo': 'Nuevo Cliente'
    })

@login_required
def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado correctamente')
            return redirect('ventas:lista_clientes')
    else:
        form = ClienteForm(instance=cliente)
    
    return render(request, 'ventas/formulario_cliente.html', {
        'form': form,
        'cliente': cliente,
        'titulo': f'Editar Cliente: {cliente.nombre_completo}'
    })
