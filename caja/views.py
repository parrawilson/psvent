from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .models import Caja, MovimientoCaja,SesionCaja
from .forms import CajaForm, AperturaCajaForm, MovimientoCajaForm, CierreCajaForm
from usuarios.models import PerfilUsuario

from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
import datetime

from django.db.models import Sum, Q
from django.utils.timezone import make_aware

@login_required
def lista_cajas(request):
    cajas = Caja.objects.select_related('responsable', 'responsable__usuario').all()
    return render(request, 'caja/lista_cajas.html', {
        'cajas': cajas,
        'titulo': 'Lista de Cajas'
    })

@login_required
def crear_caja(request):
    if request.method == 'POST':
        form = CajaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Caja creada correctamente')
            return redirect('caja:lista_cajas')
    else:
        form = CajaForm()
    
    return render(request, 'caja/formulario_caja.html', {
        'form': form,
        'titulo': 'Crear Nueva Caja'
    })

@login_required
def abrir_caja(request, caja_id):
    caja = get_object_or_404(Caja, pk=caja_id)
    
    if request.method == 'POST':
        form = AperturaCajaForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    caja.abrir(request.user.perfil, form.cleaned_data['saldo_inicial'])
                    messages.success(request, f'Caja {caja.nombre} abierta correctamente')
                    return redirect('caja:detalle_caja', caja_id=caja.id)
            except Exception as e:
                messages.error(request, f'Error al abrir caja: {str(e)}')
    else:
        form = AperturaCajaForm()
    
    return render(request, 'caja/apertura_caja.html', {
        'caja': caja,
        'form': form,
        'titulo': f'Abrir Caja: {caja.nombre}'
    })

@login_required
def detalle_caja(request, caja_id):
    caja = get_object_or_404(Caja, pk=caja_id)
    movimientos = MovimientoCaja.objects.filter(caja=caja).select_related(
        'responsable', 'venta', 'compra'
    ).order_by('-fecha')
    
    return render(request, 'caja/detalle_caja.html', {
        'caja': caja,
        'movimientos': movimientos,
        'titulo': f'Detalle de Caja: {caja.nombre}'
    })

@login_required
def registrar_movimiento(request, caja_id):
    caja = get_object_or_404(Caja, pk=caja_id)
    
    if request.method == 'POST':
        form = MovimientoCajaForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    movimiento = form.save(commit=False)
                    movimiento.caja = caja  # Asignación explícita
                    movimiento.responsable = request.user.perfil
                    movimiento.save()  # Ahora se manejará la sesión automáticamente
                    
                    messages.success(request, 'Movimiento registrado correctamente')
                    return redirect('caja:detalle_caja', caja_id=caja.id)
            except Exception as e:
                messages.error(request, f'Error al registrar movimiento: {str(e)}')
    else:
        form = MovimientoCajaForm()
    
    return render(request, 'caja/registrar_movimiento.html', {
        'caja': caja,
        'form': form,
        'titulo': f'Registrar Movimiento - {caja.nombre}'
    })


@login_required
def reporte_cierre_pdf(request, caja_id):
    try:
        caja = get_object_or_404(Caja, pk=caja_id)
        
        # Obtener movimientos y cálculos
        movimientos = caja.movimientos.all().order_by('-fecha')
        ingresos = sum(m.monto for m in movimientos.filter(tipo='INGRESO'))
        egresos = sum(m.monto for m in movimientos.filter(tipo='EGRESO'))
        
        context = {
            'caja': caja,
            'movimientos': movimientos,
            'ingresos': ingresos,
            'egresos': egresos,
            'fecha_reporte': datetime.datetime.now(),
            'usuario': request.user,
        }
        
        template = get_template('caja/reporte_cierre_pdf.html')
        html = template.render(context)
        
        response = HttpResponse(content_type='application/pdf')
        filename = f"Cierre_Caja_{caja.nombre}_{datetime.date.today()}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Configuración simplificada (sin duplicar 'encoding')
        pisa_status = pisa.CreatePDF(
            html,
            dest=response,
            encoding='UTF-8',  # Solo aquí una vez
            link_callback=None
        )
        
        if pisa_status.err:
            messages.error(request, 'Error al generar el PDF')
            return redirect('caja:detalle_caja', caja_id=caja.id)
            
        return response
        
    except Exception as e:
        messages.error(request, f'Error inesperado: {str(e)}')
        return redirect('caja:detalle_caja', caja_id=caja_id)



# Nuevas vistas para reportes
@login_required
def reportes_caja(request):
    cajas = Caja.objects.all()
    return render(request, 'caja/reportes/menu_reportes.html', {
        'cajas': cajas,
        'titulo': 'Reportes de Caja'
    })

@login_required
def reporte_movimientos(request):
    # Filtros
    caja_id = request.GET.get('caja')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    tipo = request.GET.get('tipo')

    # Consulta base
    movimientos = MovimientoCaja.objects.select_related(
        'caja', 'responsable__usuario'
    ).order_by('-fecha')

    # Aplicar filtros
    if caja_id:
        movimientos = movimientos.filter(caja_id=caja_id)
    if fecha_inicio:
        movimientos = movimientos.filter(fecha__gte=make_aware(
            datetime.datetime.strptime(fecha_inicio, '%Y-%m-%d')
        ))
    if fecha_fin:
        movimientos = movimientos.filter(fecha__lte=make_aware(
            datetime.datetime.strptime(fecha_fin + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
        ))
    if tipo:
        movimientos = movimientos.filter(tipo=tipo)

    # Totales
    total_ingresos = movimientos.filter(tipo='INGRESO').aggregate(
        Sum('monto'))['monto__sum'] or 0
    total_egresos = movimientos.filter(tipo='EGRESO').aggregate(
        Sum('monto'))['monto__sum'] or 0

    # PDF o HTML
    if 'exportar' in request.GET:
        context = {
            'movimientos': movimientos,
            'total_ingresos': total_ingresos,
            'total_egresos': total_egresos,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'usuario': request.user,
            'empresa_nombre': "Mi Empresa S.A.",  # Ajusta estos valores
            'empresa_direccion': "Av. Principal 123",
            'saldo_neto': total_ingresos - total_egresos,
            'fecha_reporte': datetime.datetime.now(),
            'usuario': request.user,
        }

        template = get_template('caja/reportes/reporte_movimientos_pdf.html')
        html = template.render(context)

        response = HttpResponse(content_type='application/pdf')
        filename = f"Movimientos_Caja_{fecha_inicio or 'inicio'}_{fecha_fin or 'hoy'}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # Configuración mejorada de pisa.CreatePDF()
        pisa_status = pisa.CreatePDF(
            html,
            dest=response,
            encoding='UTF-8',
            link_callback=None,
            show_error_as_pdf=True  # ¡Esto es clave para debug!
        )

        if pisa_status.err:
            messages.error(request, 'Error al generar el PDF. Revise los logs.')
            return redirect('caja:reportes_caja')
        return response

    return render(request, 'caja/reportes/reporte_movimientos.html', {
        'movimientos': movimientos,
        'cajas': Caja.objects.all(),
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'filtros': {
            'caja_id': caja_id,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'tipo': tipo,
        }
    })


@login_required
def reporte_cierres(request):
    try:
        # Filtros
        caja_id = request.GET.get('caja')
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')

        # Consulta base optimizada (sin prefetch_related si usamos iterator)
        cierres = SesionCaja.objects.filter(
            estado='CERRADA'
        ).select_related(
            'caja', 
            'responsable__usuario'
        ).order_by('-fecha_cierre')

        # Aplicar filtros con validación
        if caja_id and caja_id.isdigit():
            cierres = cierres.filter(caja_id=int(caja_id))
        
        try:
            if fecha_inicio:
                fecha_inicio_dt = make_aware(
                    datetime.datetime.strptime(fecha_inicio, '%Y-%m-%d')
                )
                cierres = cierres.filter(fecha_cierre__gte=fecha_inicio_dt)
            
            if fecha_fin:
                fecha_fin_dt = make_aware(
                    datetime.datetime.strptime(fecha_fin + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
                )
                cierres = cierres.filter(fecha_cierre__lte=fecha_fin_dt)
        except ValueError as e:
            messages.error(request, f"Formato de fecha inválido: {str(e)}")
            cierres = cierres.none()

        # Cálculo de totales optimizado
        total_ingresos = 0
        total_egresos = 0
        total_diferencia = 0

        # Opción 1: Sin iterator (para conjuntos de datos no muy grandes)
        for sesion in cierres:
            try:
                # Usamos aggregate para evitar cargar todos los movimientos
                ingresos = sesion.movimientos.filter(tipo='INGRESO').aggregate(
                    Sum('monto')
                )['monto__sum'] or 0
                egresos = sesion.movimientos.filter(tipo='EGRESO').aggregate(
                    Sum('monto')
                )['monto__sum'] or 0
                
                total_ingresos += ingresos
                total_egresos += egresos
                
                if sesion.saldo_final is not None:
                    total_diferencia += (sesion.saldo_final - (sesion.saldo_inicial + ingresos - egresos))
            except Exception as e:
                messages.warning(request, f"Error calculando totales para sesión {sesion.id}: {str(e)}")
                continue

        # Opción 2: Si necesitas iterator para grandes conjuntos de datos
        # (pero sin prefetch_related)
        # for sesion in cierres.iterator(chunk_size=2000):
        #     ... mismo código que arriba ...

        # Generación de PDF
        if 'exportar' in request.GET:
            context = {
                'sesiones': cierres,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'total_ingresos': total_ingresos,
                'total_egresos': total_egresos,
                'total_diferencia': total_diferencia,
                'fecha_reporte': datetime.datetime.now(),
                'usuario': request.user,
                'empresa_nombre': "Su Empresa",
                'empresa_direccion': "Dirección de la empresa",
            }

            try:
                template = get_template('caja/reportes/reporte_cierres_pdf.html')
                html = template.render(context)

                response = HttpResponse(content_type='application/pdf')
                filename = f"Reporte_Cierres_{fecha_inicio or 'inicio'}_{fecha_fin or 'hoy'}.pdf"
                response['Content-Disposition'] = f'attachment; filename="{filename}"'

                pdf_status = pisa.CreatePDF(
                    html,
                    dest=response,
                    encoding='UTF-8'
                )

                if pdf_status.err:
                    messages.error(request, 'Error al generar el PDF')
                    return redirect('caja:reporte_cierres')

                return response

            except Exception as e:
                messages.error(request, f'Error generando PDF: {str(e)}')
                return redirect('caja:reporte_cierres')

        # Vista HTML
        return render(request, 'caja/reportes/reporte_cierres.html', {
            'sesiones': cierres,
            'cajas': Caja.objects.all(),
            'total_ingresos': total_ingresos,
            'total_egresos': total_egresos,
            'total_diferencia': total_diferencia,
            'filtros': {
                'caja_id': caja_id,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
            }
        })

    except Exception as e:
        messages.error(request, f'Error inesperado: {str(e)}')
        return render(request, 'caja/reportes/reporte_cierres.html', {
            'sesiones': SesionCaja.objects.none(),
            'cajas': Caja.objects.all(),
            'total_ingresos': 0,
            'total_egresos': 0,
            'total_diferencia': 0,
            'filtros': {}
        })


@login_required
def cerrar_caja(request, caja_id):
    caja = get_object_or_404(Caja, pk=caja_id)
    
    if caja.estado != 'ABIERTA':
        messages.error(request, 'La caja ya está cerrada')
        return redirect('caja:detalle_caja', caja_id=caja.id)
    
    # Calcular resumen para el cierre
    movimientos = caja.movimientos.filter(
        sesion=caja.sesion_activa
    ) if caja.sesion_activa else caja.movimientos.none()
    
    ingresos = movimientos.filter(tipo='INGRESO').aggregate(
        Sum('monto'))['monto__sum'] or 0
    egresos = movimientos.filter(tipo='EGRESO').aggregate(
        Sum('monto'))['monto__sum'] or 0
    
    if request.method == 'POST':
        form = CierreCajaForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Cerrar la sesión activa primero
                    if caja.sesion_activa:
                        caja.sesion_activa.cerrar(
                            saldo_final=caja.saldo_actual,
                            observaciones=form.cleaned_data['observaciones']
                        )
                    
                    # Luego cerrar la caja
                    caja.cerrar()
                    
                    messages.success(request, f'Caja {caja.nombre} cerrada correctamente')
                    return redirect('caja:detalle_caja', caja_id=caja.id)
                    
            except Exception as e:
                messages.error(request, f'Error al cerrar caja: {str(e)}')
    else:
        form = CierreCajaForm()
    
    return render(request, 'caja/cierre_caja.html', {
        'caja': caja,
        'form': form,
        'ingresos': ingresos,
        'egresos': egresos,
        'titulo': f'Cerrar Caja: {caja.nombre}'
    })




@login_required
def reporte_sesion_pdf(request, sesion_id):
    sesion = get_object_or_404(SesionCaja, pk=sesion_id)
    
    # Calcular duración de la sesión
    duracion = sesion.fecha_cierre - sesion.fecha_apertura
    horas, remainder = divmod(duracion.total_seconds(), 3600)
    minutos, _ = divmod(remainder, 60)
    duracion_str = f"{int(horas)}h {int(minutos)}m"
    
    # Calcular totales de movimientos
    total_ingresos = sesion.movimientos.filter(tipo='INGRESO').aggregate(
        Sum('monto')
    )['monto__sum'] or 0
    
    total_egresos = sesion.movimientos.filter(tipo='EGRESO').aggregate(
        Sum('monto')
    )['monto__sum'] or 0
    
    context = {
        'sesion': sesion,
        'duracion': duracion_str,
        'fecha_reporte': datetime.datetime.now(),
        'usuario': request.user,
        'empresa_nombre': "Su Empresa S.A.",  # Reemplazar con datos reales
        'empresa_direccion': "Av. Principal 123, Lima, Perú",  # Reemplazar con datos reales
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
    }
    
    template = get_template('caja/reportes/reporte_sesion_pdf.html')
    html = template.render(context)
    
    response = HttpResponse(content_type='application/pdf')
    filename = f"Sesion_Caja_{sesion.caja.nombre}_{sesion.fecha_cierre.date()}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    pisa_status = pisa.CreatePDF(html, dest=response, encoding='UTF-8')
    
    if pisa_status.err:
        return HttpResponse('Error al generar el PDF', status=500)
    
    return response


from empresa.models import SecuenciaDocumento

def obtener_datos_caja(request, caja_id):
    try:
        caja = Caja.objects.get(pk=caja_id)
        punto_expedicion = caja.punto_expedicion
        
        # Obtener todas las secuencias disponibles para este punto de expedición
        secuencias = SecuenciaDocumento.objects.filter(
            punto_expedicion=punto_expedicion
        ).values('tipo_documento', 'siguiente_numero', 'formato')
        
        return JsonResponse({
            'codigo': punto_expedicion.get_codigo_completo(),
            'descripcion': punto_expedicion.descripcion,
            'secuencias': list(secuencias)
        })
    except Caja.DoesNotExist:
        return JsonResponse({'error': 'Caja no encontrada'}, status=404)