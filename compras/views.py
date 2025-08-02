
from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from django.forms import ValidationError, inlineformset_factory
from django.contrib.auth.decorators import login_required
from .models import OrdenCompra, DetalleOrdenCompra, Proveedor
from .forms import OrdenCompraForm, DetalleOrdenCompraForm, ProveedorForm, RecibirOrdenForm
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
        form = RecibirOrdenForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Convertir plazo_dias a entero
                    plazo_dias = form.cleaned_data.get('plazo_dias', 0)
                    if isinstance(plazo_dias, str):
                        plazo_dias = int(plazo_dias) if plazo_dias.isdigit() else 0
                    
                    orden.recibir(
                        usuario=request.user.perfil,
                        almacen=form.cleaned_data['almacen'],
                        caja=form.cleaned_data['caja'],
                        tipo_pago=form.cleaned_data['tipo_pago'],
                        tipo_documento=form.cleaned_data['tipo_documento'],
                        numero_documento=form.cleaned_data['numero_documento'],
                        timbrado=form.cleaned_data['timbrado'],
                        condicion=form.cleaned_data['condicion'],
                        plazo_dias=plazo_dias  # Aseguramos que es un entero
                    )
                    messages.success(request, 'Orden recibida y stock actualizado correctamente')
                    return redirect('compras:detalle_orden', orden_id=orden.id)
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Error al recibir la orden: {str(e)}')
    else:
        form = RecibirOrdenForm(user=request.user)
    
    return render(request, 'compras/recibir_orden.html', {
        'orden': orden,
        'form': form,
        'titulo': f'Recibir Orden: {orden.numero}'
    })

@login_required
def detalle_orden_compra(request, orden_id):
    orden = get_object_or_404(OrdenCompra, pk=orden_id)
    return render(request, 'compras/detalle_orden.html', {
        'orden': orden,
        'titulo': f'Detalle de Orden: {orden.numero}'
    })





from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from .models import CuentaPorPagar, PagoProveedor, OrdenCompra
from .forms import PagoProveedorForm
from caja.models import Caja

@login_required
def lista_cuentas_por_pagar(request):
    # Filtros
    estado = request.GET.get('estado', 'todas')
    query = request.GET.get('q', '')
    
    cuentas = CuentaPorPagar.objects.select_related(
        'orden_compra', 
        'orden_compra__proveedor'
    ).order_by('fecha_vencimiento')
    
    # Aplicar filtros
    if estado != 'todas':
        cuentas = cuentas.filter(estado=estado)
    
    if query:
        cuentas = cuentas.filter(
            Q(orden_compra__numero__icontains=query) |
            Q(orden_compra__proveedor__razon_social__icontains=query) |
            Q(orden_compra__proveedor__ruc__icontains=query)
        )
    
    context = {
        'cuentas': cuentas,
        'estados': CuentaPorPagar.ESTADO_CHOICES,
        'estado_actual': estado,
        'query': query,
    }
    return render(request, 'compras/cuentas_por_pagar/lista.html', context)

@login_required
def detalle_cuenta_por_pagar(request, pk):
    cuenta = get_object_or_404(
        CuentaPorPagar.objects.select_related(
            'orden_compra',
            'orden_compra__proveedor'
        ), 
        pk=pk
    )
    
    pagos = cuenta.pagos.all().select_related('caja')
    
    context = {
        'cuenta': cuenta,
        'pagos': pagos,
    }
    return render(request, 'compras/cuentas_por_pagar/detalle.html', context)

@login_required
def registrar_pago_proveedor(request, pk):
    cuenta = get_object_or_404(CuentaPorPagar, pk=pk)
    
    if request.method == 'POST':
        form = PagoProveedorForm(request.user, request.POST, cuenta=cuenta)  # Pasa la cuenta al formulario
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    pago = form.save(commit=False)
                    pago.cuenta = cuenta  # Asigna la cuenta antes de guardar
                    
                    pago.save()
                    messages.success(request, 'Pago registrado correctamente')
                    return redirect('compras:detalle_cuenta_por_pagar', pk=cuenta.pk)
                    
            except Exception as e:
                messages.error(request, f'Error al registrar el pago: {str(e)}')
    else:
        form = PagoProveedorForm(
            request.user, 
            initial={
                'monto': cuenta.saldo_pendiente,
                'fecha_pago': timezone.now().date()
            },
            cuenta=cuenta  # Pasa la cuenta al formulario
        )
    
    return render(request, 'compras/cuentas_por_pagar/registrar_pago.html', {
        'cuenta': cuenta,
        'form': form,
    })

from .models import MovimientoCaja
@login_required
def eliminar_pago_proveedor(request, pk):
    pago = get_object_or_404(PagoProveedor.objects.select_related('cuenta', 'movimiento_caja'), pk=pk)
    cuenta_id = pago.cuenta.id
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 1. Revertir movimiento de caja si existe
                if pago.movimiento_caja:
                    # Verificar que la caja esté abierta
                    if pago.movimiento_caja.caja.estado != 'ABIERTA':
                        messages.error(request, 'No se puede revertir el pago porque la caja asociada no está abierta')
                        return redirect('compras:detalle_cuenta_por_pagar', pk=cuenta_id)
                    
                    # Crear movimiento de reversión (ingreso)
                    movimiento_reversion = MovimientoCaja.objects.create(
                        caja=pago.movimiento_caja.caja,
                        tipo='INGRESO',
                        monto=pago.monto,
                        responsable=request.user.perfil,
                        descripcion=f"Reversión de pago OC-{pago.cuenta.orden_compra.numero}",
                        comprobante=f"REV-{pago.comprobante or ''}"
                    )
                
                # 2. Actualizar saldos de la cuenta
                cuenta = pago.cuenta
                cuenta.saldo_pendiente += pago.monto
                
                # Si estaba marcada como pagada, volver a estado anterior
                if cuenta.estado == 'PAGADA':
                    cuenta.estado = 'VENCIDA' if cuenta.esta_vencida else 'PENDIENTE'
                    cuenta.fecha_pago = None
                    cuenta.orden_compra.estado = 'RECIBIDA'
                    cuenta.orden_compra.save()
                
                cuenta.save()
                
                # 3. Eliminar el pago (esto eliminará también la relación con movimiento_caja)
                pago.delete()
                
                messages.success(request, 'Pago eliminado y movimiento de caja revertido correctamente')
        except Exception as e:
            messages.error(request, f'Error al eliminar el pago: {str(e)}')
        
        return redirect('compras:detalle_cuenta_por_pagar', pk=cuenta_id)
    
    return render(request, 'compras/cuentas_por_pagar/confirmar_eliminar_pago.html', {
        'pago': pago,
        'cuenta': pago.cuenta  # Pasamos la cuenta al template por si es necesario
    })