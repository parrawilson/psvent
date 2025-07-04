
from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from django.forms import inlineformset_factory
from django.contrib.auth.decorators import login_required
from .models import OrdenCompra, DetalleOrdenCompra, Proveedor
from .forms import OrdenCompraForm, DetalleOrdenCompraForm, ProveedorForm
from usuarios.models import PerfilUsuario
from almacen.models import Almacen


@login_required
def lista_proveedores(request):
    proveedor = Proveedor.objects.all()
    return render(request, 'proveedores/lista.html', {'proveedores': proveedor})

@login_required
def registrar_proveedor(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedro registrado exitosamente')
            return redirect('compras:lista_proveedores')
    else:
        form = ProveedorForm
    return render(request,'proveedores/formulario.html', {
        'form': form,
        'modo': 'registrar',
        'titulo': 'Registrar Proveedor',
    })


@login_required
def editar_proveedor(request, proveedor_id):
    proveedor= get_object_or_404(Proveedor, pk= proveedor_id)
    if request.method == 'POST':
        form= ProveedorForm(request.POST, instance= proveedor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor actualizado exitosamente')
            return redirect('compras:lista_proveedores')
    else:
        form= ProveedorForm(instance=proveedor)
    
    return render(request,'proveedores/formulario.html',
                  {
                      'form':form,
                      'modo': 'editar',
                      'titulo': 'Editar Proveedor',
                      'proveedor': proveedor,
                  }
                  )



@login_required
def eliminar_proveedor(request, proveedor_id):
    if request.method== 'POST':
        proveedor= get_object_or_404(Proveedor, pk= proveedor_id)
        proveedor.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success':True})
        else:
            return redirect('compras:lista_proveedores')
    return HttpResponseNotAllowed(['POST'])






@login_required
def lista_ordenes_compra(request):
    ordenes = OrdenCompra.objects.select_related('proveedor', 'creado_por').order_by('-fecha')
    return render(request, 'compras/lista_ordenes.html', {
        'ordenes': ordenes,
        'titulo': 'Órdenes de Compra'
    })

@login_required
def crear_orden_compra(request):
    DetalleFormSet = inlineformset_factory(
        OrdenCompra, 
        DetalleOrdenCompra, 
        form=DetalleOrdenCompraForm,
        extra=1,
        can_delete=True
    )
    
    if request.method == 'POST':
        form = OrdenCompraForm(request.POST)
        formset = DetalleFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                # Crear la orden
                orden = form.save(commit=False)
                orden.creado_por = request.user.perfil
                
                # Generar número de orden (puedes implementar tu propia lógica)
                from datetime import datetime
                orden.numero = f"OC-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                
                orden.save()
                
                # Guardar los detalles
                detalles = formset.save(commit=False)
                for detalle in detalles:
                    detalle.orden = orden
                    detalle.save()
                 
                # Calcular totales
                orden.calcular_totales()
                
                messages.success(request, 'Orden de compra creada correctamente')
                return redirect('compras:lista_ordenes')
    else:
        form = OrdenCompraForm()
        formset = DetalleFormSet(request.POST or None, prefix='detalles')
    
    return render(request, 'compras/formulario_orden.html', {
        'form': form,
        'formset': formset,
        'titulo': 'Nueva Orden de Compra'
    })









@login_required
def editar_orden_compra(request, orden_id):
    orden = get_object_or_404(OrdenCompra, pk=orden_id)
    
    # Solo permitir edición si está en estado BORRADOR
    if orden.estado != 'BORRADOR':
        messages.error(request, 'Solo se pueden editar órdenes en estado Borrador')
        return redirect('compras:lista_ordenes')
    
    DetalleFormSet = inlineformset_factory(
        OrdenCompra, 
        DetalleOrdenCompra, 
        form=DetalleOrdenCompraForm,
        extra=1,
        can_delete=True
    )
    
    if request.method == 'POST':
        form = OrdenCompraForm(request.POST, instance=orden)
        formset = DetalleFormSet(request.POST, instance=orden)
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()
                orden.calcular_totales()
                
                messages.success(request, 'Orden de compra actualizada correctamente')
                return redirect('compras:lista_ordenes')
    else:
        form = OrdenCompraForm(instance=orden)
        formset = DetalleFormSet(instance=orden)
    
    return render(request, 'compras/formulario_orden.html', {
        'form': form,
        'formset': formset,
        'orden': orden,
        'titulo': f'Editar Orden: {orden.numero}'
    })

@login_required
def aprobar_orden_compra(request, orden_id):
    orden = get_object_or_404(OrdenCompra, pk=orden_id)
    
    if orden.estado == 'BORRADOR':
        orden.aprobar(request.user.perfil)
        messages.success(request, 'Orden aprobada correctamente')
    else:
        messages.error(request, 'La orden no puede ser aprobada en su estado actual')
    
    return redirect('compras:lista_ordenes')

@login_required
def recibir_orden_compra(request, orden_id):
    orden = get_object_or_404(OrdenCompra, pk=orden_id)
    
    if request.method == 'POST':
        almacen_id = request.POST.get('almacen')
        almacen = get_object_or_404(Almacen, pk=almacen_id)
        
        try:
            orden.recibir(request.user.perfil, almacen)
            messages.success(request, 'Orden recibida y stock actualizado correctamente')
        except Exception as e:
            messages.error(request, f'Error al recibir la orden: {str(e)}')
        
        return redirect('compras:lista_ordenes')
    
    # Si es GET, mostrar formulario para seleccionar almacén
    almacenes = Almacen.objects.filter(activo=True)
    return render(request, 'compras/recibir_orden.html', {
        'orden': orden,
        'almacenes': almacenes,
        'titulo': f'Recibir Orden: {orden.numero}'
    })

@login_required
def detalle_orden_compra(request, orden_id):
    orden = get_object_or_404(OrdenCompra, pk=orden_id)
    return render(request, 'compras/detalle_orden.html', {
        'orden': orden,
        'titulo': f'Detalle de Orden: {orden.numero}'
    })

# Tus vistas existentes para proveedores...

