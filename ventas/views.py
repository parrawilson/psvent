from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.forms import ValidationError, inlineformset_factory,BooleanField,CheckboxInput
from .models import Venta, DetalleVenta, Cliente, Timbrado
from .forms import VentaForm, DetalleVentaForm, ClienteForm, FinalizarVentaForm, TimbradoForm
from usuarios.models import PerfilUsuario
from almacen.models import Stock, Almacen
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
                    # Establecer tipo basado en lo que se seleccionó
                    if detalle.producto:
                        detalle.tipo = 'PRODUCTO'
                    elif detalle.servicio:
                        detalle.tipo = 'SERVICIO'
                    
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
        'titulo': 'Nueva Venta',
        'modo': 'crear'
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
        extra=0,
        can_delete=True
    )
    
    if request.method == 'POST':
        form = VentaForm(request.POST, instance=venta)
        formset = DetalleFormSet(request.POST, instance=venta)
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                
                # Guardar los detalles y establecer tipo
                detalles = formset.save(commit=False)
                for detalle in detalles:
                    if detalle.producto:
                        detalle.tipo = 'PRODUCTO'
                    elif detalle.servicio:
                        detalle.tipo = 'SERVICIO'
                    detalle.save()
                
                # Eliminar detalles marcados para borrar
                for obj in formset.deleted_objects:
                    obj.delete()
                
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
        'titulo': f'Editar Venta: {venta.numero}',
        'modo': 'editar'
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
        for detalle in venta.detalles.select_related('producto', 'servicio', 'almacen'):
            if detalle.tipo == 'PRODUCTO':
                stock = Stock.objects.filter(
                    producto=detalle.producto,
                    almacen=detalle.almacen
                ).first()
                
                if not stock or stock.cantidad < detalle.cantidad:
                    messages.error(request, 
                        f'Stock insuficiente para {detalle.producto.nombre}. Disponible: {stock.cantidad if stock else 0}'
                    )
                    return redirect('ventas:editar_venta', venta_id=venta.id)
            
            elif detalle.tipo == 'SERVICIO' and detalle.servicio.tipo == 'COMPUESTO':
                almacen_servicio = detalle.almacen_servicio or Almacen.objects.filter(es_principal=True).first()
                if not almacen_servicio:
                    messages.error(request, 'No se encontró almacén para los componentes del servicio')
                    return redirect('ventas:editar_venta', venta_id=venta.id)
                
                for componente in detalle.servicio.componentes.select_related('producto'):
                    cantidad_necesaria = componente.cantidad * detalle.cantidad
                    stock = Stock.objects.filter(
                        producto=componente.producto,
                        almacen=almacen_servicio
                    ).first()
                    
                    if not stock or stock.cantidad < cantidad_necesaria:
                        messages.error(request,
                            f'Stock insuficiente de {componente.producto.nombre} para el servicio {detalle.servicio.nombre}. '
                            f'Necesario: {cantidad_necesaria}, Disponible: {stock.cantidad if stock else 0}'
                        )
                        return redirect('ventas:editar_venta', venta_id=venta.id)
    except Exception as e:
        messages.error(request, f'Error al verificar stock: {str(e)}')
        logger.error(f'Error al verificar stock para venta {venta.id}: {str(e)}', exc_info=True)
        return redirect('ventas:editar_venta', venta_id=venta.id)
    
    # Procesar formulario de finalización
    if request.method == 'POST':
        form = FinalizarVentaForm(request.POST, venta=venta)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Asignar datos específicos para crédito
                    if form.cleaned_data['condicion'] == '2':  # CRÉDITO
                        venta.entrega_inicial = form.cleaned_data.get('entrega_inicial', 0)
                        venta.dia_vencimiento_cuotas = form.cleaned_data.get('dia_vencimiento', 5)
                        venta.fecha_primer_vencimiento = form.cleaned_data.get('fecha_primer_vencimiento')
                        venta.numero_cuotas = form.cleaned_data.get('numero_cuotas', 1)
                        venta.monto_cuota = form.cleaned_data.get('monto_cuota', 0)
                    
                    # Finalizar la venta (incluye movimientos de caja e inventario)
                    venta.finalizar(
                        caja=form.cleaned_data['caja'],
                        tipo_pago=form.cleaned_data['tipo_pago'],
                        tipo_documento=form.cleaned_data['tipo_documento'],
                        condicion=form.cleaned_data['condicion'],
                        timbrado=form.cleaned_data.get('timbrado')
                    )
                    
                    # Generar documento electrónico si aplica
                    generar_doc = form.cleaned_data.get('generar_documento', False)
                    
                    if generar_doc:
                        documento = SifenService.generar_documento(venta)
                        
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
                    
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Error al finalizar venta: {str(e)}')
                logger.error(f'Error al finalizar venta {venta.id}: {str(e)}', exc_info=True)
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario')
    else:
        form = FinalizarVentaForm(venta=venta)
    
    # Mostrar opción de documento electrónico solo si aplica
    if venta.cliente and venta.cliente.tipo_documento in ['1', '3']:  # Cédula paraguaya o extranjera
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
        'detalles': venta.detalles.select_related('producto', 'servicio', 'almacen'),
        'total': venta.total,
        'puede_generar_documento': venta.cliente and venta.cliente.tipo_documento in ['1', '3']
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







from django.db.models import Sum
from .models import CuentaPorCobrar, PagoCuota, Venta
from caja.models import MovimientoCaja
from .forms import PagoCuotaForm
from django.utils import timezone


@login_required
def menu_ctas_cobrar(request):
    return render(request, 'ventas/cuentas_por_cobrar/menu_ctas_cobrar.html', {
        'titulo': 'Menú Cuentas por Cobrar'
    })

@login_required
def lista_cuentas_por_cobrar(request):
    # Filtramos por cuotas pendientes o vencidas por defecto
    cuentas = CuentaPorCobrar.objects.filter(
        venta__estado='FINALIZADA'
    ).select_related(
        'venta', 'venta__cliente'
    ).order_by('fecha_vencimiento')

    # Filtros adicionales
    estado = request.GET.get('estado')
    if estado:
        cuentas = cuentas.filter(estado=estado)
    
    cliente = request.GET.get('cliente')
    if cliente:
        cuentas = cuentas.filter(venta__cliente__nombre_completo__icontains=cliente)
    
    vencidas = cuentas.filter(estado='VENCIDA')
    pendientes = cuentas.filter(estado='PENDIENTE')
    parciales = cuentas.filter(estado='PARCIAL')

    context = {
        'cuentas': cuentas,
        'vencidas': vencidas,
        'pendientes': pendientes,
        'parciales': parciales,
        'titulo': 'Gestión de Cuentas por Cobrar'
    }
    return render(request, 'ventas/cuentas_por_cobrar/lista_cuentas_por_cobrar.html', context)

@login_required
def detalle_cuenta(request, cuenta_id):
    cuenta = get_object_or_404(
        CuentaPorCobrar.objects.select_related(
            'venta', 'venta__cliente', 'venta__vendedor'
        ), 
        pk=cuenta_id
    )
    pagos = cuenta.pagos.all().order_by('-fecha_pago')
    
    context = {
        'cuenta': cuenta,
        'pagos': pagos,
        'titulo': f'Detalle de Cuenta - Venta {cuenta.venta.numero}'
    }
    return render(request, 'ventas/cuentas_por_cobrar/detalle_cuenta.html', context)

@login_required
@transaction.atomic
def registrar_pago(request, cuenta_id):
    cuenta = get_object_or_404(
        CuentaPorCobrar.objects.select_related('venta', 'venta__cliente', 'venta__caja'), 
        pk=cuenta_id
    )
    
    # Verificar estado de la cuenta
    if cuenta.estado == 'PAGADA':
        messages.warning(request, 'Esta cuenta ya está completamente pagada')
        return redirect('ventas:detalle_cuenta', cuenta_id=cuenta.id)
    
    if request.method == 'POST':
        form = PagoCuotaForm(request.POST, cuenta=cuenta)
        if form.is_valid():
            try:
                monto = form.cleaned_data['monto']
                caja = form.cleaned_data['caja']
                
                # Validar que el monto no exceda el saldo
                if monto > cuenta.saldo:
                    messages.error(request, f'El monto excede el saldo pendiente. Saldo actual: Gs. {cuenta.saldo:,.2f}')
                else:
                    with transaction.atomic():
                        # Registrar el pago
                        pago = PagoCuota.objects.create(
                            cuenta=cuenta,
                            monto=monto,
                            fecha_pago=form.cleaned_data['fecha_pago'],
                            tipo_pago=form.cleaned_data['tipo_pago'],
                            notas=form.cleaned_data['notas'],
                            registrado_por=request.user.perfil,
                            caja=caja
                        )
                        
                        # Generar número de recibo
                        pago.generar_numero_recibo()
                        
                        # Actualizar saldo y estado de la cuenta
                        cuenta.saldo -= monto
                        cuenta.actualizar_estado()
                        
                        # Si se completó el pago, registrar fecha
                        if cuenta.estado == 'PAGADA' and not cuenta.fecha_pago:
                            cuenta.fecha_pago = form.cleaned_data['fecha_pago']
                        
                        cuenta.save()
                        
                        # Registrar movimiento de caja si es en efectivo
                        if form.cleaned_data['tipo_pago'] == 'EFECTIVO':
                            MovimientoCaja.objects.create(
                                caja=caja,
                                tipo='INGRESO',
                                monto=monto,
                                responsable=request.user.perfil,
                                descripcion=f"Pago cuota {cuenta.numero_cuota} - Venta {cuenta.venta.numero}",
                                venta=cuenta.venta,
                                comprobante=f"P-{pago.id}"
                            )
                        



                        # Generar comisiones para cobradores si el pago fue registrado por un cobrador
                        if request.user.perfil.es_cobrador:
                            configuraciones = ConfiguracionComisionCobrador.objects.filter(
                                cobrador=request.user.perfil,
                                activo=True
                            )
                            
                            for config in configuraciones:
                                monto_comision = config.calcular_comision(monto)
                                if monto_comision > 0:
                                    ComisionCobrador.objects.create(
                                        pago=pago,
                                        cobrador=request.user.perfil,
                                        configuracion=config,
                                        monto=monto_comision
                                    )



                        
                        messages.success(request, 
                            f'Pago registrado correctamente. '
                            f'Nuevo saldo: Gs. {cuenta.saldo:,.2f}',
                            extra_tags='success'
                        )
                        return redirect('ventas:detalle_cuenta', cuenta_id=cuenta.id)
            
            except Exception as e:
                messages.error(request, 
                    f'Error al registrar pago: {str(e)}',
                    extra_tags='danger'
                )
                logger.error(f'Error al registrar pago: {str(e)}', exc_info=True)
    else:
        form = PagoCuotaForm(initial={
            'fecha_pago': timezone.now().date(),
            'monto': cuenta.saldo,
            'caja': cuenta.venta.caja if cuenta.venta.caja else None
        }, cuenta=cuenta)
    
    context = {
        'cuenta': cuenta,
        'form': form,
        'titulo': f'Registrar Pago - Cuenta {cuenta.numero_cuota}'
    }
    return render(request, 'ventas/cuentas_por_cobrar/registrar_pago.html', context)


from django.db.models import Q
from decimal import Decimal, InvalidOperation
from .forms import BuscarClienteForm, ConfiguracionPagoForm, PagoCuentaForm


@login_required
def cobros_rapidos(request):
    # Obtener todas las cajas abiertas
    cajas_abiertas = Caja.objects.filter(estado='ABIERTA')
    
    # Inicializar variables
    cliente = None
    cuentas = []
    forms_pago = []
    total_pagado = Decimal('0.00')
    pagos_realizados = []
    
    # Formulario de búsqueda de cliente
    buscar_cliente_form = BuscarClienteForm(request.GET or None)
    
    # Procesar búsqueda de cliente
    if 'buscar_cliente' in request.GET and buscar_cliente_form.is_valid():
        query = buscar_cliente_form.cleaned_data['q']
        if query:
            clientes = Cliente.objects.filter(
                Q(nombre_completo__icontains=query) | 
                Q(numero_documento__icontains=query)
            ).order_by('nombre_completo')
            
            if clientes.exists():
                cliente = clientes.first()
                cuentas = CuentaPorCobrar.objects.filter(
                    venta__cliente=cliente,
                    estado__in=['PENDIENTE', 'VENCIDA', 'PARCIAL']
                ).select_related('venta').order_by('fecha_vencimiento')
                
                # Preparar formularios para cada cuenta con monto inicial 0
                forms_pago = [
                    (cuenta, PagoCuentaForm(prefix=f'cuenta_{cuenta.id}', cuenta=cuenta))
                    for cuenta in cuentas
                ]
    
    # Formulario de configuración de pagos
    configuracion_form = ConfiguracionPagoForm(
        cajas_abiertas=cajas_abiertas,
        data=request.POST or None
    )
    
    # Procesar registro de pagos
    if request.method == 'POST' and 'registrar_pagos' in request.POST and configuracion_form.is_valid():
        try:
            with transaction.atomic():
                caja = configuracion_form.cleaned_data['caja']
                fecha_pago = configuracion_form.cleaned_data['fecha_pago']
                tipo_pago = configuracion_form.cleaned_data['tipo_pago']
                notas = configuracion_form.cleaned_data['notas']
                
                # Validar formularios de pago y contar montos > 0
                forms_pago_validados = []
                montos_validos = 0
                
                for cuenta in cuentas:
                    form = PagoCuentaForm(
                        data=request.POST,
                        prefix=f'cuenta_{cuenta.id}',
                        cuenta=cuenta
                    )
                    if form.is_valid():
                        monto = form.cleaned_data['monto']
                        if monto > 0:
                            montos_validos += 1
                        forms_pago_validados.append((cuenta, form))
                    else:
                        raise ValidationError(f"Error en el monto para la cuenta {cuenta.numero_cuota}: {form.errors}")
                
                # Validar que al menos un pago tenga monto > 0
                if montos_validos == 0:
                    raise ValidationError("Debe ingresar al menos un pago con monto mayor a cero")
                
                # Procesar cada pago válido con monto > 0
                for cuenta, form in forms_pago_validados:
                    monto = form.cleaned_data['monto']
                    
                    if monto > 0:
                        # Registrar pago
                        pago = PagoCuota.objects.create(
                            cuenta=cuenta,
                            monto=monto,
                            fecha_pago=fecha_pago,
                            tipo_pago=tipo_pago,
                            notas=notas,
                            registrado_por=request.user.perfil,
                            caja=caja
                        )
                        
                        # Generar número de recibo
                        pago.generar_numero_recibo()
                        
                        # Actualizar cuenta
                        cuenta.saldo -= monto
                        cuenta.actualizar_estado()
                        if cuenta.estado == 'PAGADA' and not cuenta.fecha_pago:
                            cuenta.fecha_pago = fecha_pago
                        cuenta.save()
                        
                        # Registrar movimiento de caja si es efectivo
                        if tipo_pago == 'EFECTIVO':
                            MovimientoCaja.objects.create(
                                caja=caja,
                                tipo='INGRESO',
                                monto=monto,
                                responsable=request.user.perfil,
                                descripcion=f"Pago cuota {cuenta.numero_cuota} - Venta {cuenta.venta.numero}",
                                venta=cuenta.venta,
                                comprobante=f"PAGO-{pago.id}"
                            )
                        
                        # Generar comisiones para cobradores si el pago fue registrado por un cobrador
                        if request.user.perfil.es_cobrador:
                            configuraciones = ConfiguracionComisionCobrador.objects.filter(
                                cobrador=request.user.perfil,
                                activo=True
                            )
                            
                            for config in configuraciones:
                                monto_comision = config.calcular_comision(monto)
                                if monto_comision > 0:
                                    ComisionCobrador.objects.create(
                                        pago=pago,
                                        cobrador=request.user.perfil,
                                        configuracion=config,
                                        monto=monto_comision
                                    )
                        
                        # Guardar pago realizado para mostrar
                        pagos_realizados.append({
                            'cuenta': cuenta,
                            'pago': pago,
                            'monto': monto
                        })
                        total_pagado += monto
                
                messages.success(request, f'Se registraron {len(pagos_realizados)} pagos por un total de Gs. {total_pagado:,.2f}')
                
                # Mantener al cliente seleccionado para continuar
                if pagos_realizados:
                    cliente = pagos_realizados[0]['cuenta'].venta.cliente
                    cuentas = CuentaPorCobrar.objects.filter(
                        venta__cliente=cliente,
                        estado__in=['PENDIENTE', 'VENCIDA', 'PARCIAL']
                    ).select_related('venta').order_by('fecha_vencimiento')
                    forms_pago = [
                        (cuenta, PagoCuentaForm(prefix=f'cuenta_{cuenta.id}', cuenta=cuenta))
                        for cuenta in cuentas
                    ]
                
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error al registrar pagos: {str(e)}')
            logger.error(f'Error en registro rápido de pagos: {str(e)}', exc_info=True)
    
    context = {
        'buscar_cliente_form': buscar_cliente_form,
        'configuracion_form': configuracion_form,
        'forms_pago': forms_pago,
        'cliente': cliente,
        'cuentas': cuentas,
        'pagos_realizados': pagos_realizados,
        'total_pagado': total_pagado,
        'fecha_hoy': timezone.now().date().strftime('%Y-%m-%d'),
        'titulo': 'Registro Rápido de Pagos'
    }
    return render(request, 'ventas/cuentas_por_cobrar/cobros_rapidos.html', context)











@login_required
def lista_pagos(request):
    pagos = PagoCuota.objects.filter(
        cancelado=False
    ).select_related(
        'cuenta', 'cuenta__venta', 'cuenta__venta__cliente', 'registrado_por'
    ).order_by('-fecha_pago')
    
    # Filtros
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    tipo_pago = request.GET.get('tipo_pago')
    
    if fecha_desde:
        pagos = pagos.filter(fecha_pago__gte=fecha_desde)
    if fecha_hasta:
        pagos = pagos.filter(fecha_pago__lte=fecha_hasta)
    if tipo_pago:
        pagos = pagos.filter(tipo_pago=tipo_pago)
    
    context = {
        'pagos': pagos,
        'titulo': 'Histórico de Pagos',
        'total_pagos': pagos.aggregate(Sum('monto'))['monto__sum'] or 0,
        'puede_cancelar': request.user.has_perm('ventas.cancelar_pago')  # Asegúrate de crear este permiso
    }
    return render(request, 'ventas/cuentas_por_cobrar/lista_pagos.html', context)


@login_required
@require_POST
def cancelar_pago(request, pago_id):
    pago = get_object_or_404(PagoCuota, pk=pago_id)
    
    if not request.user.has_perm('ventas.cancelar_pago'):
        messages.error(request, 'No tienes permiso para cancelar pagos')
        return redirect('ventas:lista_pagos')
    
    motivo = request.POST.get('motivo', 'Cancelación solicitada por el usuario')
    
    try:
        with transaction.atomic():
            pago.cancelar(request.user.perfil, motivo)
            messages.success(request, f'Pago #{pago.id} cancelado correctamente')
    except ValidationError as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, f'Error al cancelar pago: {str(e)}')
        logger.error(f'Error cancelando pago {pago_id}: {str(e)}', exc_info=True)
    
    return redirect('ventas:lista_pagos')











from django.template.loader import get_template
from xhtml2pdf import pisa
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

@login_required
def imprimir_recibo(request, pago_id, tipo='normal'):
    pago = get_object_or_404(
        PagoCuota.objects.select_related(
            'cuenta', 'cuenta__venta', 'cuenta__venta__cliente',
            'registrado_por', 'caja', 'caja__punto_expedicion'
        ),
        pk=pago_id
    )
    
    if not pago.numero_recibo:
        pago.generar_numero_recibo()
    
    context = {
        'pago': pago,
        'empresa': request.user.perfil.empresa,
        'fecha_impresion': timezone.now().strftime("%d/%m/%Y %H:%M"),
        'numero_recibo_completo': pago.formato_numero_recibo,
    }
    
    # Seleccionar template según tipo de impresión
    template_name = 'ventas/recibo_pago_tk.html' if tipo == 'ticket' else 'ventas/recibo_pago.html'
    template = get_template(template_name)
    html = template.render(context)
    
    response = HttpResponse(content_type='application/pdf')
    filename = f"Recibo-{pago.formato_numero_recibo}-{'TK' if tipo == 'ticket' else 'N'}.pdf"
    response['Content-Disposition'] = f'filename="{filename}"'
    
    pisa_status = pisa.CreatePDF(html, dest=response, encoding='UTF-8')
    
    if pisa_status.err:
        return HttpResponse('Error al generar el PDF')
    return response



# views.py (añadir al final)

from .models import ComisionVenta, ConfiguracionComision

@login_required
def menu_comsiones(request):
    return render(request, 'ventas/comisiones/menu.html', {
        'titulo': 'Menú Comisiones'
    })

@login_required
def lista_comisiones(request):
    comisiones = ComisionVenta.objects.select_related(
        'venta', 'venta__cliente', 'vendedor'
    ).order_by('-creado')
    
    # Filtros
    estado = request.GET.get('estado')
    vendedor_id = request.GET.get('vendedor')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if estado:
        comisiones = comisiones.filter(estado=estado)
    if vendedor_id:
        comisiones = comisiones.filter(vendedor_id=vendedor_id)
    if fecha_desde:
        comisiones = comisiones.filter(venta__fecha__gte=fecha_desde)
    if fecha_hasta:
        comisiones = comisiones.filter(venta__fecha__lte=fecha_hasta)
    
    vendedores = PerfilUsuario.objects.filter(
        comisiones_ventas__isnull=False
    ).distinct()
    
    context = {
        'comisiones': comisiones,
        'vendedores': vendedores,
        'titulo': 'Gestión de Comisiones',
        'total_pendiente': comisiones.filter(estado='PENDIENTE').aggregate(Sum('monto'))['monto__sum'] or 0,
        'total_pagado': comisiones.filter(estado='PAGADA').aggregate(Sum('monto'))['monto__sum'] or 0,
    }
    return render(request, 'ventas/comisiones/lista_comisiones.html', context)

from caja.models import Caja
from .forms import ConfiguracionComisionForm


@login_required
def configurar_comisiones(request):
    if request.method == 'POST':
        form = ConfiguracionComisionForm(request.POST)
        if form.is_valid():
            try:
                config = form.save(commit=False)
                # Desactivar configuraciones previas del mismo tipo
                ConfiguracionComision.objects.filter(
                    vendedor=config.vendedor,
                    tipo=config.tipo,
                    activo=True
                ).update(activo=False)
                
                config.save()
                messages.success(request, 'Configuración guardada correctamente')
                return redirect('ventas:configurar_comisiones')
            except Exception as e:
                messages.error(request, f'Error al guardar: {str(e)}')
    else:
        form = ConfiguracionComisionForm()

    configuraciones = ConfiguracionComision.objects.filter(activo=True).select_related('vendedor')
    
    return render(request, 'ventas/comisiones/configurar_comisiones.html', {
        'form': form,
        'configuraciones': configuraciones,
        'titulo': 'Configuración de Comisiones'
    })





from django.db.models import Q
@login_required
def lista_configuraciones_comision(request):
    configuraciones = ConfiguracionComision.objects.filter(activo=True).select_related('vendedor')
    
    # Filtros
    vendedor_id = request.GET.get('vendedor')
    tipo = request.GET.get('tipo')
    
    if vendedor_id:
        configuraciones = configuraciones.filter(vendedor_id=vendedor_id)
    if tipo:
        configuraciones = configuraciones.filter(tipo=tipo)
    
    vendedores = PerfilUsuario.objects.filter(
        Q(es_vendedor=True) | Q(usuario__is_staff=True))
    
    context = {
        'configuraciones': configuraciones,
        'vendedores': vendedores,
        'tipos_comision': ConfiguracionComision.TIPO_COMISION_CHOICES,
        'titulo': 'Configuraciones de Comisiones'
    }
    return render(request, 'ventas/comisiones/lista.html', context)




@login_required
@transaction.atomic
def pagar_comision(request, comision_id):
    comision = get_object_or_404(ComisionVenta, pk=comision_id)
    
    if comision.estado != 'PENDIENTE':
        messages.warning(request, 'Esta comisión ya ha sido pagada o cancelada')
        return redirect('ventas:lista_comisiones')
    
    if request.method == 'POST':
        fecha_pago = request.POST.get('fecha_pago', timezone.now().date())
        caja_id = request.POST.get('caja')
        
        try:
            caja = Caja.objects.get(pk=caja_id, estado='ABIERTA')
            
            with transaction.atomic():
                # Generar un comprobante único con timestamp
                timestamp = int(timezone.now().timestamp())
                comprobante = f"COM-{comision.id}-{timestamp}"
                
                # Registrar movimiento en caja
                MovimientoCaja.objects.create(
                    caja=caja,
                    tipo='EGRESO',
                    monto=comision.monto,
                    responsable=request.user.perfil,
                    descripcion=f"Pago comisión venta {comision.venta.numero}",
                    comprobante=comprobante  # Usamos el nuevo comprobante único
                )
                
                # Marcar la comisión como pagada
                comision.pagar(fecha_pago)
                
                messages.success(request, f'Comisión pagada y registrada en caja {caja.nombre}')
                return redirect('ventas:lista_comisiones')
                
        except Caja.DoesNotExist:
            messages.error(request, 'La caja seleccionada no existe o no está abierta')
        except Exception as e:
            messages.error(request, f'Error al pagar comisión: {str(e)}')
            logger.error(f'Error al pagar comisión {comision_id}: {str(e)}', exc_info=True)
    
    cajas_abiertas = Caja.objects.filter(estado='ABIERTA')
    
    return render(request, 'ventas/comisiones/confirmar_pago_comision.html', {
        'comision': comision,
        'cajas': cajas_abiertas,
        'titulo': f'Pagar Comisión - {comision}',
        'fecha_hoy': timezone.now().date().strftime('%Y-%m-%d')
    })





@login_required
@require_POST
@transaction.atomic
def revertir_pago_comision(request, comision_id):
    comision = get_object_or_404(ComisionVenta, pk=comision_id)
    motivo = request.POST.get('motivo', 'Reversión solicitada por el usuario')
    
    try:
        comision.revertir_pago(usuario=request.user.perfil, motivo=motivo)
        messages.success(request, 'Pago de comisión revertido correctamente')
    except ValidationError as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, f'Error al revertir pago: {str(e)}')
        logger.error(f'Error al revertir comisión {comision_id}: {str(e)}', exc_info=True)
    
    return redirect('ventas:lista_comisiones')


@login_required
def detalle_comision_vendedor(request, comision_id):
    """Vista para mostrar el detalle de una comisión a vendedor"""
    comision = get_object_or_404(
        ComisionVenta.objects.select_related(
            'venta', 'venta__cliente', 'vendedor', 'configuracion'
        ),
        pk=comision_id
    )
    
    # Obtener movimientos de caja relacionados
    movimientos = MovimientoCaja.objects.filter(
        Q(comprobante__startswith=f"COM-{comision.id}-") |
        Q(comprobante__startswith=f"COM-REV-{comision.id}-")
    ).order_by('-fecha')
    
    context = {
        'comision': comision,
        'movimientos': movimientos,
        'titulo': f'Detalle Comisión #{comision.id}'
    }
    
    return render(request, 'ventas/comisiones/detalle.html', context)






















from .forms import ConfiguracionComisionCobradorForm
from .models import ComisionCobrador, ConfiguracionComisionCobrador

@login_required
def menu_comisiones_cobradores(request):
    return render(request, 'ventas/comisiones_cobradores/menu.html', {
        'titulo': 'Menú Comisiones Cobradores'
    })



@login_required
def lista_configuraciones_comision_cobradores(request):
    configuraciones = ConfiguracionComisionCobrador.objects.select_related('cobrador')
    
    # Filtros
    cobrador_id = request.GET.get('cobrador')
    
    if cobrador_id:
        configuraciones = configuraciones.filter(cobrador_id=cobrador_id)
    
    cobradores = PerfilUsuario.objects.filter(
        Q(es_cobrador=True) | Q(usuario__is_staff=True))
    
    context = {
        'configuraciones': configuraciones,
        'cobradores': cobradores,
        'titulo': 'Configuraciones de Comisiones para Cobradores'
    }
    return render(request, 'ventas/comisiones_cobradores/lista_configuraciones.html', context)


@login_required
def configurar_comisiones_cobradores(request):
    if request.method == 'POST':
        form = ConfiguracionComisionCobradorForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    config = form.save(commit=False)
                    # Desactivar configuraciones previas del mismo cobrador
                    ConfiguracionComisionCobrador.objects.filter(
                        cobrador=config.cobrador,
                        activo=True
                    ).update(activo=False)
                    
                    config.save()
                    messages.success(request, 'Configuración guardada correctamente')
                    return redirect('ventas:lista_configurar_comisiones_cobradores')
            except Exception as e:
                messages.error(request, f'Error al guardar: {str(e)}')
                logger.error(f'Error al crear configuración comisión cobrador: {str(e)}', exc_info=True)
    else:
        form = ConfiguracionComisionCobradorForm()
    
    return render(request, 'ventas/comisiones_cobradores/configurar.html', {
        'form': form,
        'modo': 'crear',
        'titulo': 'Nueva Configuración de Comisión para Cobrador'
    })


@login_required
@require_POST
def desactivar_configuracion_comision_cobrador(request, config_id):
    config = get_object_or_404(ConfiguracionComisionCobrador, pk=config_id)
    config.activo = False
    config.save()
    messages.success(request, 'Configuración desactivada correctamente')
    return redirect('ventas:lista_configuraciones_comision_cobradores')


@login_required
@transaction.atomic
def editar_configuracion_comision_cobrador(request, config_id):
    config = get_object_or_404(ConfiguracionComisionCobrador, pk=config_id)
    
    if request.method == 'POST':
        form = ConfiguracionComisionCobradorForm(request.POST, instance=config)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Si cambió el cobrador, desactivar configuraciones previas
                    if 'cobrador' in form.changed_data:
                        ConfiguracionComisionCobrador.objects.filter(
                            cobrador=form.cleaned_data['cobrador'],
                            activo=True
                        ).exclude(pk=config_id).update(activo=False)
                    
                    form.save()
                    messages.success(request, 'Configuración actualizada correctamente')
                    return redirect('ventas:lista_configurar_comisiones_cobradores')
            except Exception as e:
                messages.error(request, f'Error al actualizar: {str(e)}')
                logger.error(f'Error al editar configuración comisión cobrador {config_id}: {str(e)}', exc_info=True)
    else:
        form = ConfiguracionComisionCobradorForm(instance=config)
    
    return render(request, 'ventas/comisiones_cobradores/configurar.html', {
        'form': form,
        'modo': 'editar',
        'configuracion': config,
        'titulo': f'Editar Configuración - {config.cobrador}'
    })


@login_required
def lista_comisiones_cobradores(request):
    comisiones = ComisionCobrador.objects.select_related(
        'pago', 'pago__cuenta', 'pago__cuenta__venta', 'cobrador'
    ).order_by('-creado')
    
    # Filtros
    estado = request.GET.get('estado')
    cobrador_id = request.GET.get('cobrador')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if estado:
        comisiones = comisiones.filter(estado=estado)
    if cobrador_id:
        comisiones = comisiones.filter(cobrador_id=cobrador_id)
    if fecha_desde:
        comisiones = comisiones.filter(creado__gte=fecha_desde)
    if fecha_hasta:
        comisiones = comisiones.filter(creado__lte=fecha_hasta)
    
    cobradores = PerfilUsuario.objects.filter(
        comisiones_cobros__isnull=False
    ).distinct()
    
    context = {
        'comisiones': comisiones,
        'cobradores': cobradores,
        'titulo': 'Gestión de Comisiones para Cobradores',
        'total_comisiones': comisiones.aggregate(Sum('monto'))['monto__sum'] or 0,
        'total_pendiente': comisiones.filter(estado='PENDIENTE').aggregate(Sum('monto'))['monto__sum'] or 0,
        'total_pagado': comisiones.filter(estado='PAGADA').aggregate(Sum('monto'))['monto__sum'] or 0,
    }
    return render(request, 'ventas/comisiones_cobradores/lista.html', context)

@login_required
@transaction.atomic
def pagar_comision_cobrador(request, comision_id):
    comision = get_object_or_404(ComisionCobrador, pk=comision_id)
    
    if comision.estado != 'PENDIENTE':
        messages.warning(request, 'Esta comisión ya ha sido pagada o cancelada')
        return redirect('ventas:lista_comisiones_cobradores')
    
    if request.method == 'POST':
        fecha_pago = request.POST.get('fecha_pago', timezone.now().date())
        caja_id = request.POST.get('caja')
        
        try:
            caja = Caja.objects.get(pk=caja_id, estado='ABIERTA')
            
            with transaction.atomic():
                # Generar un comprobante único con timestamp
                timestamp = int(timezone.now().timestamp())
                comprobante = f"COM-COB-{comision.id}-{timestamp}"
                
                # Registrar movimiento en caja
                MovimientoCaja.objects.create(
                    caja=caja,
                    tipo='EGRESO',
                    monto=comision.monto,
                    responsable=request.user.perfil,
                    descripcion=f"Pago comisión cobro #{comision.pago.id}",
                    comprobante=comprobante
                )
                
                # Marcar la comisión como pagada
                comision.pagar(fecha_pago)
                
                messages.success(request, f'Comisión pagada y registrada en caja {caja.nombre}')
                return redirect('ventas:lista_comisiones_cobradores')
                
        except Caja.DoesNotExist:
            messages.error(request, 'La caja seleccionada no existe o no está abierta')
        except Exception as e:
            messages.error(request, f'Error al pagar comisión: {str(e)}')
            logger.error(f'Error al pagar comisión cobrador {comision_id}: {str(e)}', exc_info=True)
    
    cajas_abiertas = Caja.objects.filter(estado='ABIERTA')
    
    return render(request, 'ventas/comisiones_cobradores/confirmar_pago.html', {
        'comision': comision,
        'cajas': cajas_abiertas,
        'titulo': f'Pagar Comisión - {comision}',
        'fecha_hoy': timezone.now().date().strftime('%Y-%m-%d')
    })

@login_required
@require_POST
@transaction.atomic
def revertir_pago_comision_cobrador(request, comision_id):
    comision = get_object_or_404(ComisionCobrador, pk=comision_id)
    motivo = request.POST.get('motivo', 'Reversión solicitada por el usuario')
    
    try:
        comision.revertir_pago(usuario=request.user.perfil, motivo=motivo)
        messages.success(request, 'Pago de comisión revertido correctamente')
    except ValidationError as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, f'Error al revertir pago: {str(e)}')
        logger.error(f'Error al revertir comisión cobrador {comision_id}: {str(e)}', exc_info=True)
    
    return redirect('ventas:lista_comisiones_cobradores')




@login_required
def detalle_comision_cobrador(request, comision_id):
    """Vista para mostrar el detalle de una comisión a cobrador"""
    comision = get_object_or_404(
        ComisionCobrador.objects.select_related(
            'pago', 'pago__cuenta', 'pago__cuenta__venta', 
            'pago__cuenta__venta__cliente', 'cobrador', 'configuracion'
        ),
        pk=comision_id
    )
    
    # Obtener movimientos de caja relacionados
    movimientos = MovimientoCaja.objects.filter(
        Q(comprobante__startswith=f"COM-COB-{comision.id}-") |
        Q(comprobante__startswith=f"COM-COB-REV-{comision.id}-")
    ).order_by('-fecha')
    
    context = {
        'comision': comision,
        'movimientos': movimientos,
        'titulo': f'Detalle Comisión #{comision.id}'
    }
    
    return render(request, 'ventas/comisiones_cobradores/detalle.html', context)



from .forms import PagoComisionCobradorForm, BuscarCobradorForm

@login_required
def pagos_rapidos_comisiones_cobradores(request):
    """Vista para pagos rápidos de comisiones a cobradores"""
    # Obtener cajas abiertas
    cajas_abiertas = Caja.objects.filter(estado='ABIERTA')
    
    # Inicializar variables
    cobrador = None
    comisiones = []
    forms_pago = []
    total_pagado = Decimal('0.00')
    pagos_realizados = []
    
    # Formulario de búsqueda
    buscar_form = BuscarCobradorForm(request.GET or None)
    
    # Procesar búsqueda
    if 'buscar_cobrador' in request.GET and buscar_form.is_valid():
        query = buscar_form.cleaned_data['q']
        if query:
            cobradores = PerfilUsuario.objects.filter(
                Q(usuario__first_name__icontains=query) |
                Q(usuario__last_name__icontains=query) |
                Q(usuario__username__icontains=query),
                es_cobrador=True
            ).order_by('usuario__first_name', 'usuario__last_name')
            
            if cobradores.exists():
                cobrador = cobradores.first()
                comisiones = ComisionCobrador.objects.filter(
                    cobrador=cobrador,
                    estado__in=['PENDIENTE', 'PARCIAL']
                ).select_related(
                    'pago', 'pago__cuenta', 'pago__cuenta__venta'
                ).order_by('creado')
                
                # Preparar formularios para cada comisión
                forms_pago = [
                    (comision, PagoComisionCobradorForm(prefix=f'comision_{comision.id}', comision=comision))
                    for comision in comisiones
                ]
    
    # Formulario de configuración de pago
    configuracion_form = ConfiguracionPagoForm(
        cajas_abiertas=cajas_abiertas,
        data=request.POST or None
    )
    
    # Procesar pagos
    if request.method == 'POST' and 'registrar_pagos' in request.POST and configuracion_form.is_valid():
        try:
            with transaction.atomic():
                caja = configuracion_form.cleaned_data['caja']
                fecha_pago = configuracion_form.cleaned_data['fecha_pago']
                tipo_pago = configuracion_form.cleaned_data['tipo_pago']
                notas = configuracion_form.cleaned_data['notas']
                
                # Validar formularios de pago
                forms_pago_validados = []
                montos_validos = 0
                
                for comision, form in forms_pago:
                    form = PagoComisionCobradorForm(
                        data=request.POST,
                        prefix=f'comision_{comision.id}',
                        comision=comision
                    )
                    if form.is_valid():
                        monto = form.cleaned_data['monto']
                        if monto > 0:
                            montos_validos += 1
                        forms_pago_validados.append((comision, form))
                    else:
                        raise ValidationError(f"Error en el monto para la comisión {comision.id}: {form.errors}")
                
                if montos_validos == 0:
                    raise ValidationError("Debe ingresar al menos un pago con monto mayor a cero")
                
                # Procesar pagos válidos
                for comision, form in forms_pago_validados:
                    monto = form.cleaned_data['monto']
                    
                    if monto > 0:
                        # Calcular saldo pendiente antes del pago
                        saldo_pendiente = comision.monto - comision.monto_pagado
                        
                        # Validar que el monto no exceda el saldo pendiente
                        if monto > saldo_pendiente:
                            raise ValidationError(
                                f"El monto excede el saldo pendiente para la comisión {comision.id}. "
                                f"Saldo pendiente: Gs. {saldo_pendiente:,.2f}"
                            )
                        
                        # Registrar movimiento de caja
                        timestamp = int(timezone.now().timestamp())
                        comprobante = f"COM-COB-{comision.id}-{timestamp}"
                        
                        MovimientoCaja.objects.create(
                            caja=caja,
                            tipo='EGRESO',
                            monto=monto,
                            responsable=request.user.perfil,
                            descripcion=f"Pago comisión cobro #{comision.pago.id}",
                            comprobante=comprobante
                        )
                        
                        # Actualizar la comisión (método pagar ahora maneja parciales)
                        comision.pagar(monto, fecha_pago)
                        
                        # Registrar el pago realizado
                        pagos_realizados.append({
                            'comision': comision,
                            'monto': monto,
                            'saldo_anterior': saldo_pendiente,
                            'nuevo_saldo': saldo_pendiente - monto
                        })
                        total_pagado += monto
                
                messages.success(request, 
                    f'Se registraron {len(pagos_realizados)} pagos por un total de Gs. {total_pagado:,.2f}'
                )
                
                # Recargar datos si hubo pagos
                if pagos_realizados:
                    cobrador = pagos_realizados[0]['comision'].cobrador
                    comisiones = ComisionCobrador.objects.filter(
                        cobrador=cobrador,
                        estado__in=['PENDIENTE', 'PARCIAL']
                    ).select_related(
                        'pago', 'pago__cuenta', 'pago__cuenta__venta'
                    ).order_by('creado')
                    forms_pago = [
                        (comision, PagoComisionCobradorForm(prefix=f'comision_{comision.id}', comision=comision))
                        for comision in comisiones
                    ]
                
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error al registrar pagos: {str(e)}')
            logger.error(f'Error en pagos rápidos a cobradores: {str(e)}', exc_info=True)
    
    context = {
        'buscar_form': buscar_form,
        'configuracion_form': configuracion_form,
        'forms_pago': forms_pago,
        'cobrador': cobrador,
        'comisiones': comisiones,
        'pagos_realizados': pagos_realizados,
        'total_pagado': total_pagado,
        'titulo': 'Pagos Rápidos a Cobradores'
    }
    return render(request, 'ventas/comisiones_cobradores/pagos_rapidos.html', context)





# Añadir al final de views.py
from .forms import BuscarVendedorForm, PagoComisionVendedorForm

@login_required
def pagos_rapidos_comisiones_vendedores(request):
    """Vista para pagos rápidos de comisiones a vendedores con soporte para pagos parciales"""
    # Obtener cajas abiertas
    cajas_abiertas = Caja.objects.filter(estado='ABIERTA')
    
    # Inicializar variables
    vendedor = None
    comisiones = []
    forms_pago = []
    total_pagado = Decimal('0.00')
    pagos_realizados = []
    
    # Formulario de búsqueda
    buscar_form = BuscarVendedorForm(request.GET or None)
    
    # Procesar búsqueda
    if 'buscar_vendedor' in request.GET and buscar_form.is_valid():
        query = buscar_form.cleaned_data['q']
        if query:
            vendedores = PerfilUsuario.objects.filter(
                Q(usuario__first_name__icontains=query) |
                Q(usuario__last_name__icontains=query) |
                Q(usuario__username__icontains=query),
                es_vendedor=True
            ).order_by('usuario__first_name', 'usuario__last_name')
            
            if vendedores.exists():
                vendedor = vendedores.first()
                comisiones = ComisionVenta.objects.filter(
                    vendedor=vendedor,
                    estado__in=['PENDIENTE', 'PARCIAL']
                ).select_related(
                    'venta', 'venta__cliente', 'configuracion'
                ).order_by('creado')
                
                # Preparar formularios para cada comisión
                forms_pago = [
                    (comision, PagoComisionVendedorForm(prefix=f'comision_{comision.id}', comision=comision))
                    for comision in comisiones
                ]
    
    # Formulario de configuración de pago
    configuracion_form = ConfiguracionPagoForm(
        cajas_abiertas=cajas_abiertas,
        data=request.POST or None
    )
    
    # Procesar pagos
    if request.method == 'POST' and 'registrar_pagos' in request.POST and configuracion_form.is_valid():
        try:
            with transaction.atomic():
                caja = configuracion_form.cleaned_data['caja']
                fecha_pago = configuracion_form.cleaned_data['fecha_pago']
                tipo_pago = configuracion_form.cleaned_data['tipo_pago']
                notas = configuracion_form.cleaned_data['notas']
                
                # Validar formularios de pago
                forms_pago_validados = []
                montos_validos = 0
                
                for comision, form in forms_pago:
                    form = PagoComisionVendedorForm(
                        data=request.POST,
                        prefix=f'comision_{comision.id}',
                        comision=comision
                    )
                    if form.is_valid():
                        monto = form.cleaned_data['monto']
                        if monto > 0:
                            montos_validos += 1
                        forms_pago_validados.append((comision, form))
                    else:
                        raise ValidationError(f"Error en el monto para la comisión {comision.id}: {form.errors}")
                
                if montos_validos == 0:
                    raise ValidationError("Debe ingresar al menos un pago con monto mayor a cero")
                
                # Procesar pagos válidos
                for comision, form in forms_pago_validados:
                    monto = form.cleaned_data['monto']
                    
                    if monto > 0:
                        # Validar que el monto no exceda el saldo pendiente
                        if monto > comision.saldo_pendiente:
                            raise ValidationError(
                                f"El monto excede el saldo pendiente para la comisión {comision.id}. "
                                f"Saldo pendiente: Gs. {comision.saldo_pendiente:,.2f}"
                            )
                        
                        # Registrar movimiento de caja
                        timestamp = int(timezone.now().timestamp())
                        comprobante = f"COM-VEN-{comision.id}-{timestamp}"
                        
                        MovimientoCaja.objects.create(
                            caja=caja,
                            tipo='EGRESO',
                            monto=monto,
                            responsable=request.user.perfil,
                            descripcion=f"Pago comisión venta #{comision.venta.numero}",
                            comprobante=comprobante
                        )
                        
                        # Actualizar la comisión
                        comision.pagar(monto, fecha_pago)
                        
                        # Registrar el pago realizado
                        pagos_realizados.append({
                            'comision': comision,
                            'monto': monto,
                            'saldo_anterior': comision.saldo_pendiente + monto,  # Saldo antes del pago
                            'nuevo_saldo': comision.saldo_pendiente  # Saldo después del pago
                        })
                        total_pagado += monto
                
                messages.success(request, 
                    f'Se registraron {len(pagos_realizados)} pagos por un total de Gs. {total_pagado:,.2f}'
                )
                
                # Recargar datos si hubo pagos
                if pagos_realizados:
                    vendedor = pagos_realizados[0]['comision'].vendedor
                    comisiones = ComisionVenta.objects.filter(
                        vendedor=vendedor,
                        estado__in=['PENDIENTE', 'PARCIAL']
                    ).select_related(
                        'venta', 'venta__cliente', 'configuracion'
                    ).order_by('creado')
                    forms_pago = [
                        (comision, PagoComisionVendedorForm(prefix=f'comision_{comision.id}', comision=comision))
                        for comision in comisiones
                    ]
                
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error al registrar pagos: {str(e)}')
            logger.error(f'Error en pagos rápidos a vendedores: {str(e)}', exc_info=True)
    
    context = {
        'buscar_form': buscar_form,
        'configuracion_form': configuracion_form,
        'forms_pago': forms_pago,
        'vendedor': vendedor,
        'comisiones': comisiones,
        'pagos_realizados': pagos_realizados,
        'total_pagado': total_pagado,
        'titulo': 'Pagos Rápidos a Vendedores'
    }
    return render(request, 'ventas/comisiones/pagos_rapidos.html', context)



#Sección de Notas de Créditos

from django.forms import inlineformset_factory
from .forms import NotaCreditoForm, DetalleNotaCreditoForm
from .models import NotaCredito, DetalleNotaCredito


# En views.py - modificar la vista crear_nota_credito
@login_required
def crear_nota_credito(request, venta_id=None):
    venta = get_object_or_404(Venta, pk=venta_id, estado='FINALIZADA') if venta_id else None
    
    # Configurar el formset
    DetalleFormSet = inlineformset_factory(
        NotaCredito,
        DetalleNotaCredito,
        form=DetalleNotaCreditoForm,
        extra=1,
        can_delete=True
    )
    
    if request.method == 'POST':
        form = NotaCreditoForm(request.POST, user=request.user)
        formset = DetalleFormSet(request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    nota_credito = form.save(commit=False)
                    nota_credito.creado_por = request.user.perfil
                    nota_credito.numero = f"NC-{timezone.now().strftime('%Y%m%d-%H%M%S')}"
                    
                    # Validación adicional del motivo
                    motivo = form.cleaned_data.get('motivo', '').strip()
                    if len(motivo) < 10:
                        raise ValidationError("El motivo debe tener al menos 10 caracteres")
                    
                    nota_credito.save()
                    
                    # Ahora asignamos la instancia al formset y validamos
                    formset = DetalleFormSet(request.POST, instance=nota_credito)
                    
                    if formset.is_valid():
                        formset.save()
                        
                        # Calcular total
                        nota_credito.total = sum(d.subtotal for d in nota_credito.detalles.all())
                        nota_credito.save()
                        
                        messages.success(request, 'Nota de crédito creada correctamente')
                        return redirect('ventas:finalizar_nota_credito', nota_credito_id=nota_credito.id)
                    else:
                        # Si el formset no es válido, mostrar errores
                        for error in formset.non_form_errors():
                            messages.error(request, error)
                        for form in formset:
                            for field, errors in form.errors.items():
                                for error in errors:
                                    messages.error(request, f'Error en {field}: {error}')
                        # Eliminar la nota de crédito creada ya que el formset falló
                        nota_credito.delete()
                        raise ValidationError("Errores en los detalles de la nota de crédito")
                        
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Error al crear nota de crédito: {str(e)}')
                logger.error(f'Error al crear nota de crédito: {str(e)}', exc_info=True)
    else:
        initial = {'venta': venta} if venta else {}
        form = NotaCreditoForm(initial=initial, user=request.user)
        formset = DetalleFormSet(queryset=DetalleNotaCredito.objects.none())
    
    # Preparar datos para el template
    detalles_venta = {}
    if venta:
        detalles_venta = {
            detalle.id: {
                'detalle': detalle,
                'producto': detalle.producto,
                'servicio': detalle.servicio,
                'cantidad': float(detalle.cantidad),
                'precio_unitario': float(detalle.precio_unitario)
            }
            for detalle in venta.detalles.select_related('producto', 'servicio').all()
        }
    
    return render(request, 'ventas/notas_credito/formulario.html', {
        'form': form,
        'formset': formset,
        'titulo': 'Nueva Nota de Crédito',
        'venta': venta,
        'detalles_venta': detalles_venta,
    })




@login_required
def finalizar_nota_credito(request, nota_credito_id):
    nota_credito = get_object_or_404(NotaCredito, pk=nota_credito_id)
    
    if nota_credito.estado != 'BORRADOR':
        messages.error(request, 'Solo se pueden finalizar notas de crédito en estado Borrador')
        return redirect('ventas:detalle_nota_credito', nota_credito_id=nota_credito.id)
    
    # Verificar que tenga detalles
    if not nota_credito.detalles.exists():
        messages.error(request, 'No se puede finalizar una nota de crédito sin detalles')
        return redirect('ventas:editar_nota_credito', nota_credito_id=nota_credito.id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Primero validar todos los detalles antes de procesar
                for detalle in nota_credito.detalles.all():
                    # Validar formato decimal usando el mismo approach que en ventas
                    try:
                        # Convertir a Decimal con precisión controlada
                        cantidad = Decimal(str(detalle.cantidad)).quantize(Decimal('0.001'))
                        precio = Decimal(str(detalle.precio_unitario)).quantize(Decimal('0.01'))
                        
                        # Actualizar con valores redondeados
                        detalle.cantidad = cantidad
                        detalle.precio_unitario = precio
                        detalle.subtotal = (cantidad * precio).quantize(Decimal('0.01'))
                        
                    except (ValueError, InvalidOperation) as e:
                        raise ValidationError(f'Error en formato decimal del detalle: {str(e)}')
                    
                    detalle.save()
                
                # Recalcular el total (similar a como se hace en ventas)
                total = sum(detalle.subtotal for detalle in nota_credito.detalles.all())
                nota_credito.total = total.quantize(Decimal('0.01'))
                
                # Validar caja (como se hace en finalizar_venta)
                if not nota_credito.caja or nota_credito.caja.estado != 'ABIERTA':
                    raise ValidationError('La caja debe estar abierta para registrar notas de crédito')
                
                # Finalizar la nota de crédito
                nota_credito.finalizar()
                
                messages.success(request, 'Nota de crédito finalizada correctamente')
                return redirect('ventas:detalle_nota_credito', nota_credito_id=nota_credito.id)
                
        except ValidationError as e:
            # === CÓDIGO DE DEBUG AQUÍ ===
            import traceback
            logger.error(f"ValidationError completo: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Mostrar errores específicos de campo
            if hasattr(e, 'error_dict'):
                for field, errors in e.error_dict.items():
                    for error in errors:
                        messages.error(request, f'Error en {field}: {error}')
            else:
                messages.error(request, f'Error: {str(e)}')
            # === FIN CÓDIGO DE DEBUG ===
            
        except Exception as e:
            error_msg = f'Error inesperado al finalizar nota de crédito: {str(e)}'
            messages.error(request, error_msg)
            logger.error(f'Error al finalizar nota de crédito {nota_credito.id}: {str(e)}', exc_info=True)
    
    # Preparar datos para el template
    context = {
        'nota_credito': nota_credito,
        'titulo': f'Finalizar Nota de Crédito: {nota_credito.numero}',
        'detalles': nota_credito.detalles.select_related(
            'detalle_venta', 
            'detalle_venta__producto', 
            'detalle_venta__servicio',
            'detalle_venta__almacen'
        ),
        'total': nota_credito.total,
    }
    
    return render(request, 'ventas/notas_credito/finalizar.html', context)



@login_required
def detalle_nota_credito(request, nota_credito_id):
    nota_credito = get_object_or_404(
        NotaCredito.objects.select_related('venta', 'venta__cliente', 'creado_por', 'caja'),
        pk=nota_credito_id
    )
    
    return render(request, 'ventas/notas_credito/detalle.html', {
        'nota_credito': nota_credito,
        'titulo': f'Detalle Nota de Crédito: {nota_credito.numero}'
    })

@login_required
@require_POST
def cancelar_nota_credito(request, nota_credito_id):
    nota_credito = get_object_or_404(NotaCredito, pk=nota_credito_id)
    
    if nota_credito.estado != 'FINALIZADA':
        messages.error(request, 'Solo se pueden cancelar notas de crédito finalizadas')
        return redirect('ventas:detalle_nota_credito', nota_credito_id=nota_credito.id)
    
    motivo = request.POST.get('motivo', f"Cancelación solicitada por {request.user.get_full_name()}")
    
    try:
        with transaction.atomic():
            if motivo:
                nota_credito.notas = f"\n--- CANCELACIÓN ---\nMotivo: {motivo}\nUsuario: {request.user.get_full_name()}\nFecha: {timezone.now().strftime('%Y-%m-%d %H:%M')}\n\n{nota_credito.notas or ''}"
            
            nota_credito.cancelar(usuario=request.user.perfil)
            messages.success(request, f'Nota de crédito {nota_credito.numero} cancelada correctamente')
            
    except ValidationError as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, f'Error al cancelar nota de crédito: {str(e)}')
    
    return redirect('ventas:detalle_nota_credito', nota_credito_id=nota_credito.id)

@login_required
def lista_notas_credito(request):
    notas_credito = NotaCredito.objects.select_related(
        'venta', 'venta__cliente', 'creado_por'
    ).order_by('-fecha')
    
    # Filtros
    estado = request.GET.get('estado')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if estado:
        notas_credito = notas_credito.filter(estado=estado)
    if fecha_desde:
        notas_credito = notas_credito.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        notas_credito = notas_credito.filter(fecha__lte=fecha_hasta)
    
    context = {
        'notas_credito': notas_credito,
        'titulo': 'Listado de Notas de Crédito',
        'total_notas': notas_credito.count(),
        'total_monto': notas_credito.aggregate(Sum('total'))['total__sum'] or 0
    }
    return render(request, 'ventas/notas_credito/lista.html', context)



@login_required
def imprimir_nota_credito(request, nota_credito_id):
    nota_credito = get_object_or_404(
        NotaCredito.objects.select_related(
            'venta', 'venta__cliente', 'creado_por', 'caja', 'timbrado'
        ), 
        pk=nota_credito_id
    )
    
    # Obtener la ruta del logo de la empresa
    logo_path = None
    if request.user.perfil.empresa and request.user.perfil.empresa.logo:
        logo_path = os.path.join(settings.MEDIA_ROOT, str(request.user.perfil.empresa.logo))
    
    context = {
        'nota_credito': nota_credito,
        'empresa': request.user.perfil.empresa,
        'fecha_impresion': timezone.now().strftime("%d/%m/%Y %H:%M"),
        'logo_path': logo_path,
        'numero_documento_completo': nota_credito.formato_numero_documento,
    }
    
    # Seleccionar template según tipo de documento
    template_name = 'ventas/notas_credito/impresion/nota_credito.html'
    
    template = get_template(template_name)
    html = template.render(context)
    
    response = HttpResponse(content_type='application/pdf')
    filename = f"NotaCredito-{nota_credito.numero}.pdf"
    response['Content-Disposition'] = f'filename="{filename}"'
    
    pisa_status = pisa.CreatePDF(html, dest=response, encoding='UTF-8')
    
    if pisa_status.err:
        return HttpResponse('Error al generar el PDF')
    return response




# ventas/views_api.py
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Venta, DetalleVenta
import json

def api_detalles_venta(request, venta_id):
    """
    API que devuelve los detalles de una venta en formato JSON
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        venta = get_object_or_404(Venta, pk=venta_id)
        detalles = venta.detalles.all().select_related('producto', 'servicio', 'almacen')
        
        detalles_data = []
        for detalle in detalles:
            detalle_data = {
                'id': detalle.id,
                'tipo': detalle.tipo,
                'descripcion': str(detalle.producto) if detalle.tipo == 'PRODUCTO' else str(detalle.servicio),
                'cantidad': float(detalle.cantidad),
                'precio_unitario': float(detalle.precio_unitario),
                'subtotal': float(detalle.subtotal),
                'tasa_iva': detalle.tasa_iva,
                'producto_id': detalle.producto.id if detalle.producto else None,
                'servicio_id': detalle.servicio.id if detalle.servicio else None,
                'almacen_id': detalle.almacen.id if detalle.almacen else None,
                'almacen_nombre': str(detalle.almacen) if detalle.almacen else None,
            }
            detalles_data.append(detalle_data)
        
        response_data = {
            'venta_id': venta.id,
            'venta_numero': venta.numero,
            'cliente': str(venta.cliente) if venta.cliente else 'Consumidor Final',
            'total_venta': float(venta.total),
            'detalles': detalles_data
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({'error': f'Error al obtener detalles: {str(e)}'}, status=500)