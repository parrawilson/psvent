from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.forms import ValidationError, inlineformset_factory,BooleanField,CheckboxInput
from .models import Venta, DetalleVenta, Cliente, Timbrado
from .forms import VentaForm, DetalleVentaForm, ClienteForm, FinalizarVentaForm, TimbradoForm
from usuarios.models import PerfilUsuario
from almacen.models import Stock
import logging
from django.views.decorators.http import require_POST
from facturacion.services.sifen import SifenService



# Configuración del logger
logger = logging.getLogger(__name__)

# CRUD para Clientes
@login_required
def lista_clientes(request):
    clientes = Cliente.objects.all().order_by('nombre_completo')
    return render(request, 'ventas/lista_clientes.html', {
        'clientes': clientes,
        'titulo': 'Lista de Clientes'
    })

import json
from django.conf import settings
import os

@login_required
def crear_cliente(request):

    # Cargar el JSON de países
    file_path = os.path.join(settings.BASE_DIR, 'ventas', 'paises.json')
    with open(file_path, 'r', encoding='utf-8') as f:
        paises_json = json.load(f)


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
        'titulo': 'Nuevo Cliente',
        'modo': 'registrar',
        'paises_json': json.dumps(paises_json),  # aquí cargás el JSON al contexto
    })



@login_required
def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)

    # Cargar el JSON de países
    file_path = os.path.join(settings.BASE_DIR, 'ventas', 'paises.json')
    with open(file_path, 'r', encoding='utf-8') as f:
        paises_json = json.load(f)
    
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
        'modo': 'editar',
        'titulo': f'Editar Cliente: {cliente.nombre_completo}',
        'paises_json': json.dumps(paises_json),  # aquí cargás el JSON al contexto
    })



@login_required
def eliminar_cliente(request, cliente_id):
    if request.method== 'POST':
        cliente= get_object_or_404(Cliente, pk= cliente_id)
        cliente.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success':True})
        else:
            return redirect('ventas:lista_clientes')
    return HttpResponseNotAllowed(['POST'])




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
        extra=0,
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
                return redirect('ventas:finalizar_venta', venta_id=venta.id)
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
    
    # Validaciones iniciales
    if venta.estado != 'BORRADOR':
        messages.error(request, 'Solo se pueden finalizar ventas en estado Borrador')
        return redirect('ventas:lista_ventas')
    
    if not venta.detalles.exists():
        messages.error(request, 'No se puede finalizar una venta sin detalles')
        return redirect('ventas:editar_venta', venta_id=venta.id)
    
    # Verificar stock antes de mostrar el formulario
    try:
        for detalle in venta.detalles.all():
            stock = Stock.objects.filter(
                producto=detalle.producto,
                almacen=detalle.almacen
            ).first()
            
            if not stock or stock.cantidad < detalle.cantidad:
                messages.error(request, f'Stock insuficiente para {detalle.producto.nombre}. Disponible: {stock.cantidad if stock else 0}')
                return redirect('ventas:editar_venta', venta_id=venta.id)
    except Exception as e:
        messages.error(request, f'Error al verificar stock: {str(e)}')
        return redirect('ventas:editar_venta', venta_id=venta.id)
    
    # Procesar formulario de finalización
    if request.method == 'POST':
        form = FinalizarVentaForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Finalizar la venta (esto incluye los movimientos de caja e inventario)
                    venta.finalizar(
                        caja=form.cleaned_data['caja'],
                        tipo_pago=form.cleaned_data['tipo_pago'],
                        tipo_documento=form.cleaned_data['tipo_documento'],
                        condicion=form.cleaned_data['condicion'],
                        timbrado=form.cleaned_data.get('timbrado')
                    )
                    generar_doc = form.cleaned_data.get('generar_documento', False)
                    
                    if generar_doc:
                        
                        documento = SifenService.generar_documento(venta)
                        
                        # 3. Generar KUDE automáticamente si el documento se generó correctamente

                        if documento and documento.estado == 'VALIDADO':
                            try:
                                if SifenService.generar_kude(documento):
                                    messages.info(request, 'Documento electrónico y KUDE generados correctamente')
                                else:
                                    messages.warning(request, 'Documento generado pero no se pudo crear el KUDE')
                            except Exception as e:
                                logger.error(f'Error generando KUDE para venta {venta.id}: {str(e)}', exc_info=True)
                                messages.warning(request, 'Documento generado pero ocurrió un error al crear el KUDE')
                        
                        if documento:
                            messages.success(request, f'Documento electrónico generado: {documento.get_estado_display()}')
                    
                    messages.success(request, 'Venta finalizada correctamente')
                    return redirect('ventas:detalle_venta', venta_id=venta.id)
                    
            except Exception as e:
                messages.error(request, f'Error al finalizar venta: {str(e)}')
                logger.error(f'Error al finalizar venta {venta.id}: {str(e)}', exc_info=True)
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario')
    else:
        form = FinalizarVentaForm()
    
    # Mostrar opción de documento electrónico solo si aplica
    if venta.cliente and venta.cliente.tipo_documento in ['RUC', 'Cédula']:
        form.fields['generar_documento'] = BooleanField(
            initial=True,
            required=False,
            label='Generar documento electrónico',
            help_text='Marque para generar factura electrónica (XML y KUDE)',
            widget=CheckboxInput(attrs={'class': 'rounded'})
        )
    
    context = {
        'venta': venta,
        'form': form,
        'titulo': f'Finalizar Venta: {venta.numero}',
        'detalles': venta.detalles.select_related('producto', 'almacen'),
        'total': venta.total,
        'puede_generar_documento': venta.cliente
    }
    
    return render(request, 'ventas/finalizar_venta.html', context)



@login_required
def detalle_venta(request, venta_id):
    venta = get_object_or_404(Venta, pk=venta_id)
    return render(request, 'ventas/detalle_venta.html', {
        'venta': venta,
        'titulo': f'Detalle de Venta: {venta.numero}'
    })


# Configuración del logger
logger = logging.getLogger(__name__)

@login_required
@require_POST  # Asegura que solo se pueda acceder mediante POST
def cancelar_venta(request, venta_id):
    """
    Vista para cancelar una venta finalizada.
    Requiere autenticación y método POST.
    """
    # Obtener la venta o mostrar error 404 si no existe
    venta = get_object_or_404(Venta, pk=venta_id)
    
    # Validar estado de la venta
    if venta.estado != 'FINALIZADA':
        messages.error(request, 'Solo se pueden cancelar ventas finalizadas')
        return redirect('ventas:detalle_venta', venta_id=venta.id)
    
    # Verificar permisos (opcional, según tu sistema de permisos)
    if not request.user.has_perm('ventas.cancelar_venta'):
        messages.error(request, 'No tienes permiso para cancelar ventas')
        return redirect('ventas:detalle_venta', venta_id=venta.id)
    
    # Obtener motivo de cancelación del formulario
    motivo = request.POST.get('motivo', f"Cancelación solicitada por {request.user.get_full_name()}")
    
    try:
        with transaction.atomic():
            # Registrar motivo en las notas de la venta
            if motivo:
                venta.notas = f"\n--- CANCELACIÓN ---\nMotivo: {motivo}\nUsuario: {request.user.get_full_name()}\nFecha: {timezone.now().strftime('%Y-%m-%d %H:%M')}\n\n{venta.notas or ''}"
            
            # Ejecutar la cancelación (método del modelo)
            venta.cancelar(usuario=request.user.perfil)
            
            # Mensaje de éxito
            messages.success(request, f'Venta {venta.numero} cancelada correctamente')
            logger.info(f'Venta {venta.id} cancelada por el usuario {request.user.id}')
            
            return redirect('ventas:detalle_venta', venta_id=venta.id)
            
    except ValidationError as e:
        # Errores de validación (controlados)
        messages.error(request, f'No se pudo cancelar la venta: {str(e)}')
        logger.warning(f'Error de validación al cancelar venta {venta.id}: {str(e)}')
        
    except Exception as e:
        # Errores inesperados
        error_msg = f'Error inesperado al cancelar la venta: {str(e)}'
        messages.error(request, error_msg)
        logger.error(f'Error al cancelar venta {venta.id}: {str(e)}', exc_info=True)
        
    # Redireccionar a la vista de detalle en caso de error
    return redirect('ventas:detalle_venta', venta_id=venta.id)

@login_required
def lista_timbrados(request):
    timbrados = Timbrado.objects.all().order_by('-fecha_inicio')
    return render(request, 'ventas/lista_timbrados.html', {
        'timbrados': timbrados,
        'titulo': 'Listado de Timbrados'
    })

@login_required
def crear_timbrado(request):
    if request.method == 'POST':
        form = TimbradoForm(request.POST)
        if form.is_valid():
            timbrado = form.save()
            messages.success(request, 'Timbrado creado correctamente')
            return redirect('ventas:lista_timbrados')
    else:
        form = TimbradoForm()
    
    return render(request, 'ventas/formulario_timbrado.html', {
        'form': form,
        'titulo': 'Nuevo Timbrado',
        'modo': 'registrar'
    })

@login_required
def editar_timbrado(request, timbrado_id):
    timbrado = get_object_or_404(Timbrado, pk=timbrado_id)
    
    if request.method == 'POST':
        form = TimbradoForm(request.POST, instance=timbrado)
        if form.is_valid():
            form.save()
            messages.success(request, 'Timbrado actualizado correctamente')
            return redirect('ventas:lista_timbrados')
    else:
        form = TimbradoForm(instance=timbrado)
    
    return render(request, 'ventas/formulario_timbrado.html', {
        'form': form,
        'timbrado': timbrado,
        'modo': 'editar',
        'titulo': f'Editar Timbrado: {timbrado.numero}'
    })

@login_required
def eliminar_timbrado(request, timbrado_id):
    if request.method == 'POST':
        timbrado = get_object_or_404(Timbrado, pk=timbrado_id)
        try:
            timbrado.delete()
            messages.success(request, 'Timbrado eliminado correctamente')
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('ventas:lista_timbrados')
            
        except Exception as e:
            messages.error(request, f'Error al eliminar timbrado: {str(e)}')
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)}, status=400)
            return redirect('ventas:lista_timbrados')
    
    return HttpResponseNotAllowed(['POST'])

