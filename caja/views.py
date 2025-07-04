from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .models import Caja, MovimientoCaja
from .forms import CajaForm, AperturaCajaForm, MovimientoCajaForm, CierreCajaForm
from usuarios.models import PerfilUsuario

from django.http import HttpResponse
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
    
    if caja.estado != 'ABIERTA':
        messages.error(request, 'La caja debe estar abierta para registrar movimientos')
        return redirect('caja:detalle_caja', caja_id=caja.id)
    
    if request.method == 'POST':
        form = MovimientoCajaForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    movimiento = form.save(commit=False)
                    movimiento.caja = caja
                    movimiento.responsable = request.user.perfil
                    movimiento.save()
                    
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
def cerrar_caja(request, caja_id):
    caja = get_object_or_404(Caja, pk=caja_id)
    
    if caja.estado != 'ABIERTA':
        messages.error(request, 'La caja ya está cerrada')
        return redirect('caja:detalle_caja', caja_id=caja.id)
    
    if request.method == 'POST':
        form = CierreCajaForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    caja.cerrar()
                    messages.success(request, f'Caja {caja.nombre} cerrada correctamente')
                    return redirect('caja:detalle_caja', caja_id=caja.id)
            except Exception as e:
                messages.error(request, f'Error al cerrar caja: {str(e)}')
    else:
        form = CierreCajaForm()
    
    # Calcular resumen para el cierre
    movimientos = MovimientoCaja.objects.filter(caja=caja)
    ingresos = sum(m.monto for m in movimientos.filter(tipo='INGRESO'))
    egresos = sum(m.monto for m in movimientos.filter(tipo='EGRESO'))
    
    return render(request, 'caja/cierre_caja.html', {
        'caja': caja,
        'form': form,
        'ingresos': ingresos,
        'egresos': egresos,
        'titulo': f'Cerrar Caja: {caja.nombre}'
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
    # Filtros
    caja_id = request.GET.get('caja')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    # Consulta base
    cierres = Caja.objects.filter(
        estado='CERRADA'
    ).select_related('responsable__usuario').order_by('-fecha_cierre')

    # Aplicar filtros
    if caja_id:
        cierres = cierres.filter(id=caja_id)
    if fecha_inicio:
        cierres = cierres.filter(fecha_cierre__gte=make_aware(
            datetime.datetime.strptime(fecha_inicio, '%Y-%m-%d')
        ))
    if fecha_fin:
        cierres = cierres.filter(fecha_cierre__lte=make_aware(
            datetime.datetime.strptime(fecha_fin + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
        ))

    # PDF o HTML
    if 'exportar' in request.GET:
        context = {
            'cierres': cierres,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'fecha_reporte': datetime.datetime.now(),
            'usuario': request.user,
        }

        template = get_template('caja/reportes/reporte_cierres_pdf.html')
        html = template.render(context)

        response = HttpResponse(content_type='application/pdf')
        filename = f"Cierres_Caja_{fecha_inicio}_{fecha_fin}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        pisa.CreatePDF(html, dest=response, encoding='UTF-8')
        return response

    return render(request, 'caja/reportes/reporte_cierres.html', {
        'cierres': cierres,
        'cajas': Caja.objects.all(),
        'filtros': {
            'caja_id': caja_id,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
        }
    })