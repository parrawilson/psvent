# facturacion/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import DocumentoElectronico
from .forms import DocumentoSearchForm
from ventas.models import Venta
from django.utils import timezone
from .services.sifen import SifenService
from django.views.decorators.http import require_POST



@login_required
def lista_documentos(request):
    documentos = DocumentoElectronico.objects.select_related(
        'venta', 
        'venta__cliente'
    ).order_by('-venta__fecha')

    # Filtrado por estado
    estado = request.GET.get('estado')
    if estado:
        documentos = documentos.filter(estado=estado)

    # Búsqueda
    search_form = DocumentoSearchForm(request.GET or None)
    if search_form.is_valid() and search_form.cleaned_data.get('q'):
        q = search_form.cleaned_data['q']
        documentos = documentos.filter(
            Q(venta__numero__icontains=q) |
            Q(codigo_set__icontains=q) |
            Q(venta__cliente__nombre_completo__icontains=q)
        )

    return render(request, 'facturacion/lista_documentos.html', {
        'documentos': documentos,
        'titulo': 'Documentos Electrónicos',
        'search_form': search_form,
        'estado_seleccionado': estado
    })

@login_required
def detalle_documento(request, documento_id):
    documento = get_object_or_404(
        DocumentoElectronico.objects.select_related(
            'venta',
            'venta__cliente',
            'venta__vendedor'
        ),
        pk=documento_id
    )

    puede_reenviar = (
        documento.estado in ['ERROR', 'VALIDADO'] and
        documento.xml_firmado
    )

    return render(request, 'facturacion/detalle_documento.html', {
        'documento': documento,
        'titulo': f'Documento {documento.venta.numero}',
        'puede_reenviar': puede_reenviar
    })

@login_required
def enviar_set(request, venta_id):
    venta = get_object_or_404(Venta, pk=venta_id)
    
    if not hasattr(venta, 'documento_electronico'):
        messages.error(request, "No existe documento electrónico para esta venta")
        return redirect('ventas:detalle_venta', venta_id=venta.id)
    
    documento = venta.documento_electronico
    
    try:
        from .services import SifenService
        if SifenService.enviar_al_set(documento):
            messages.success(request, f"Documento aceptado por el SET: {documento.codigo_set}")
        else:
            messages.error(request, f"Error al enviar al SET: {documento.errores}")
    
    except Exception as e:
        messages.error(request, f"Error inesperado: {str(e)}")
    
    return redirect('facturacion:detalle_documento', documento_id=documento.id)



@require_POST
def enviar_documento_set(request, pk):
    documento = get_object_or_404(DocumentoElectronico, pk=pk)
    
    if documento.estado != 'VALIDADO':
        messages.error(request, 'Solo se pueden enviar documentos validados')
        return redirect('facturacion:detalle_documento', documento_id =pk)
    
    try:
        if SifenService.enviar_al_set(documento):
            messages.success(request, 'Documento enviado exitosamente al SET')
        else:
            messages.error(request, f'Error al enviar al SET: {documento.errores}')
    except Exception as e:
        messages.error(request, f'Error inesperado: {str(e)}')
    
    return redirect('facturacion:detalle_documento', documento_id =pk)

@require_POST
def reenviar_documento_set(request, pk):
    documento = get_object_or_404(DocumentoElectronico, pk=pk)
    
    if documento.estado not in ['VALIDADO', 'ERROR', 'RECHAZADO']:
        messages.error(request, 'No se puede reenviar este documento')
        return redirect('facturacion:detalle_documento', documento_id=pk)
    
    try:
        if SifenService.enviar_al_set(documento):
            messages.success(request, 'Documento reenviado exitosamente al SET')
        else:
            messages.error(request, f'Error al reenviar: {documento.errores}')
    except Exception as e:
        messages.error(request, f'Error inesperado: {str(e)}')
    
    return redirect('facturacion:detalle_documento', documento_id=pk)





@login_required
def reenviar_set(request, documento_id):
    documento = get_object_or_404(DocumentoElectronico, pk=documento_id)
    
    try:
        from .services import SifenService
        if SifenService.enviar_al_set(documento):
            messages.success(request, f"Documento reenviado y aceptado: {documento.codigo_set}")
        else:
            messages.error(request, f"Error al reenviar: {documento.errores}")
    
    except Exception as e:
        messages.error(request, f"Error inesperado: {str(e)}")
    
    return redirect('facturacion:detalle_documento', documento_id=documento.id)

@login_required
def descargar_xml(request, documento_id):
    documento = get_object_or_404(DocumentoElectronico, pk=documento_id)
    
    if not documento.xml_firmado:
        messages.error(request, "No hay XML disponible para descargar")
        return redirect('facturacion:detalle_documento', documento_id=documento.id)

    response = HttpResponse(documento.xml_firmado, content_type='application/xml')
    response['Content-Disposition'] = f'attachment; filename="DE-{documento.venta.numero}.xml"'
    return response



@login_required
def generar_kude(request, documento_id):
    documento = get_object_or_404(DocumentoElectronico, pk=documento_id)
    
    """""
    if not documento.codigo_set:
        messages.error(request, "El documento debe estar aceptado por el SET antes de generar el KUDE")
        return redirect('facturacion:detalle_documento', documento_id=documento.id)
    """""

    if SifenService.generar_kude(documento):
        messages.success(request, "KUDE generado correctamente")
    else:
        messages.error(request, f"Error al generar KUDE: {documento.errores}")
    
    return redirect('facturacion:detalle_documento', documento_id=documento.id)




@login_required
def descargar_kude(request, documento_id):
    documento = get_object_or_404(DocumentoElectronico, pk=documento_id)
    
    if not documento.kude_pdf:
        messages.error(request, "El KUDE no ha sido generado aún")
        return redirect('facturacion:detalle_documento', documento_id=documento.id)
    
    response = HttpResponse(documento.kude_pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="KUDE-{documento.codigo_set}.pdf"'
    return response


