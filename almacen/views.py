from django.contrib import messages
from django.forms import ValidationError
from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from .models import Producto, Servicio, Categoria, UnidadMedida,MovimientoInventario, Almacen, Stock, ComponenteServicio
from .forms import ProductoForm, CategoriaForm, UnidadMedidaForm, MovimientoInventarioForm, AlmacenForm,ConversionComplejaForm,ComponenteConversionFormSet
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone

from .forms import ServicioForm, ComponenteServicioForm, ComponenteServicioFormSet

@login_required
def lista_productos(request):
    producto = Producto.objects.all()
    return render(request, 'productos/lista.html', {'productos': producto})

@login_required
def registrar_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto registrado exitosamente')
            return redirect('almacen:lista_productos')
    else:
        form = ProductoForm
    return render(request,'productos/formulario.html', {
        'form': form,
        'modo': 'registrar',
        'titulo': 'Registrar Producto',
    })

@login_required
def editar_producto(request, producto_id):
    producto= get_object_or_404(Producto, pk= producto_id)
    if request.method == 'POST':
        form= ProductoForm(request.POST, instance= producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado exitosamente')
            return redirect('almacen:lista_productos')
    else:
        form= ProductoForm(instance=producto)
    
    return render(request,'productos/formulario.html',
                  {
                      'form':form,
                      'modo': 'editar',
                      'titulo': 'Editar Producto',
                      'producto': producto,
                  }
                  )



@login_required
def lista_servicios(request):
    servicios = Servicio.objects.all().prefetch_related('componentes')
    return render(request, 'servicios/lista.html', {'servicios': servicios})

@login_required
def registrar_servicio(request):
    if request.method == 'POST':
        form = ServicioForm(request.POST)
        formset = ComponenteServicioFormSet(request.POST, prefix='componentes')
        
        if form.is_valid() and formset.is_valid():
            servicio = form.save()
            
            # Guardar componentes del servicio
            componentes = formset.save(commit=False)
            for componente in componentes:
                componente.servicio = servicio
                componente.save()
            
            messages.success(request, 'Servicio registrado exitosamente')
            return redirect('almacen:lista_servicios')
    else:
        form = ServicioForm()
        formset = ComponenteServicioFormSet(queryset=ComponenteServicio.objects.none(), prefix='componentes')
    
    return render(request, 'servicios/formulario.html', {
        'form': form,
        'formset': formset,
        'modo': 'registrar',
        'titulo': 'Registrar Servicio',
    })

@login_required
def editar_servicio(request, servicio_id):
    servicio = get_object_or_404(Servicio, pk=servicio_id)
    
    if request.method == 'POST':
        form = ServicioForm(request.POST, instance=servicio)
        formset = ComponenteServicioFormSet(request.POST, prefix='componentes', instance=servicio)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Servicio actualizado exitosamente')
            return redirect('almacen:lista_servicios')
    else:
        form = ServicioForm(instance=servicio)
        formset = ComponenteServicioFormSet(prefix='componentes', instance=servicio)
    
    return render(request, 'servicios/formulario.html', {
        'form': form,
        'formset': formset,
        'modo': 'editar',
        'titulo': 'Editar Servicio',
        'servicio': servicio,
    })

@login_required
def eliminar_servicio(request, servicio_id):
    servicio = get_object_or_404(Servicio, pk=servicio_id)
    
    if request.method == 'POST':
        try:
            servicio.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)





def registrar_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,'Categoría registrado exitosamente')
            return redirect ('almacen:lista_categorias')
    else:
        form = CategoriaForm
    return render(request, 'categorias/formulario.html', {
        'form': form,
        'modo': 'registrar',
        'titulo': 'Registrar Categoria',
    })




@login_required
def lista_categorias(request):
    categoria = Categoria.objects.all()
    return render(request, 'categorias/lista.html', {'categorias': categoria})

@login_required
def lista_unidades_medidas(request):
    unidad_medida= UnidadMedida.objects.all()
    return render(request,'unidades_medidas/lista.html', {'unidades_medidas': unidad_medida})

@login_required
def lista_almacenes(request):
    almacenes = Almacen.objects.all()
    return render(request, 'almacenes/lista.html', {
        'almacenes': almacenes,
        'titulo': 'Lista de Almacenes'
    })



@login_required
def registrar_unidad_medida(request):
    if request.method=='POST':
        form= UnidadMedidaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Unidad de medida registrado correctamente')
            return redirect('almacen:lista_unidades_medidas')
    else:
        form = UnidadMedidaForm
    return render(request,'unidades_medidas/formulario.html',{
        'form': form,
        'modo': 'registrar',
        'titulo': 'Registar Unidad de Medida'
    })
        



@login_required
def editar_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, pk=categoria_id)
    if request.method == 'POST':
        form=CategoriaForm(request.POST, instance= categoria)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría actualizada exitosamente')
            return redirect('almacen:lista_categorias')
    else:
        form= CategoriaForm(instance=categoria)
    return render(request, 'categorias/formulario.html', {
        'form': form,
        'modo': 'editar',
        'titulo': 'Editar Categoría',
        'categoria': categoria,
    })


@login_required
def editar_unidad_medida(request, unidad_medida_id):
    unidad_medida= get_object_or_404(UnidadMedida, pk=unidad_medida_id)
    if request.method == 'POST':
        form= UnidadMedidaForm(request.POST, instance=unidad_medida)
        if form.is_valid():
            form.save()
            messages.success(request,'Unidad de Medidad actualizada exitosamente')
            return redirect('almacen:lista_unidades_medidas')
    else:
        form= UnidadMedidaForm(instance=unidad_medida)

    return render(request,'unidades_medidas/formulario.html',{
        'form': form,
        'modo': 'editar',
        'titulo': 'Editar UM',
        'unidad_medida': unidad_medida,
    })


@login_required
def eliminar_producto(request, producto_id):
    if request.method== 'POST':
        producto= get_object_or_404(Producto, pk= producto_id)
        producto.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success':True})
        else:
            return redirect('almacen:lista_productos')
    return HttpResponseNotAllowed(['POST'])

@login_required
def eliminar_categoria(request, categoria_id):
    if request.method == 'POST':
        categoria= get_object_or_404(Categoria, pk=categoria_id)
        categoria.delete()
        if request.headers.get('x-requested-with')== 'XMLHttpRequest':
            return JsonResponse({'success':True})
        else:
            return redirect('almacen:lista_categorias')
    return HttpResponseNotAllowed(['POST'])

@login_required
def eliminar_unidad_medida(request, unidad_medida_id):
    if request.method == 'POST':
        unidad_medida = get_object_or_404(UnidadMedida, pk= unidad_medida_id)
        unidad_medida.delete()
        if request.headers.get('x-requested-with')== 'XMLHttpRequest':
            return JsonResponse({'success':True})
        else:
            return redirect('almacen:lista_unidades_medidas')
    return HttpResponseNotAllowed(['POST'])


@login_required
def menu_almacenes(request):
    return render(request, 'almacenes/menu_almacenes.html', {
        'titulo': 'Menú Almacenes'
    })

@login_required
def registrar_almacen(request):
    if request.method == 'POST':
        form = AlmacenForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Almacén registrado exitosamente')
            return redirect('almacen:lista_almacenes')
    else:
        form = AlmacenForm()
    
    return render(request, 'almacenes/formulario.html', {
        'form': form,
        'modo': 'registrar',
        'titulo': 'Registrar Almacén'
    })

@login_required
def editar_almacen(request, almacen_id):
    almacen = get_object_or_404(Almacen, pk=almacen_id)
    if request.method == 'POST':
        form = AlmacenForm(request.POST, instance=almacen)
        if form.is_valid():
            form.save()
            messages.success(request, 'Almacén actualizado exitosamente')
            return redirect('almacen:lista_almacenes')
    else:
        form = AlmacenForm(instance=almacen)
    
    return render(request, 'almacenes/formulario.html', {
        'form': form,
        'modo': 'editar',
        'titulo': f'Editar Almacén: {almacen.nombre}',
        'almacen': almacen
    })

@login_required
def eliminar_almacen(request, almacen_id):
    if request.method == 'POST':
        almacen = get_object_or_404(Almacen, pk=almacen_id)
        almacen.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        messages.success(request, 'Almacén eliminado exitosamente')
        return redirect('almacen:lista_almacenes')
    return HttpResponseNotAllowed(['POST'])

@login_required
@transaction.atomic
def registrar_movimiento(request):
    if request.method == 'POST':
        form = MovimientoInventarioForm(request.POST)
        if form.is_valid():
            try:
                movimiento = form.save(commit=False)
                movimiento.usuario = request.user.perfil
                
                # Validación de stock para salidas
                if movimiento.tipo == 'SALIDA':
                    stock = Stock.objects.filter(
                        producto=movimiento.producto,
                        almacen=movimiento.almacen
                    ).first()
                    
                    if stock and stock.cantidad < movimiento.cantidad:
                        messages.error(request, f'Stock insuficiente. Disponible: {stock.cantidad}')
                        return render(request, 'movimientos/formulario.html', {
                            'form': form,
                            'modo': 'registrar',
                            'titulo': 'Registrar Movimiento'
                        })
                
                movimiento.save()
                messages.success(request, 'Movimiento registrado exitosamente')
                return redirect('almacen:lista_movimientos')
            
            except Exception as e:
                messages.error(request, f'Error al registrar movimiento: {str(e)}')
                return redirect('almacen:registrar_movimiento')
    else:
        form = MovimientoInventarioForm()
    
    return render(request, 'movimientos/formulario.html', {
        'form': form,
        'modo': 'registrar',
        'titulo': 'Registrar Movimiento'
    })


@login_required
def lista_movimientos(request):
    movimientos = MovimientoInventario.objects.select_related(
        'producto', 'almacen', 'usuario'
    ).order_by('-fecha')
    
    return render(request, 'movimientos/lista.html', {
        'movimientos': movimientos,
        'titulo': 'Historial de Movimientos'
    })


@login_required
@transaction.atomic
def editar_movimiento(request, movimiento_id):
    movimiento = get_object_or_404(MovimientoInventario, pk=movimiento_id)
    
    if request.method == 'POST':
        form = MovimientoInventarioForm(request.POST, instance=movimiento)
        if form.is_valid():
            try:
                # Guardamos los valores antiguos para reversión
                old_cantidad = movimiento.cantidad
                old_tipo = movimiento.tipo
                old_producto = movimiento.producto
                old_almacen = movimiento.almacen
                
                movimiento = form.save(commit=False)
                
                # Validación de stock para salidas
                if movimiento.tipo == 'SALIDA':
                    stock = Stock.objects.filter(
                        producto=movimiento.producto,
                        almacen=movimiento.almacen
                    ).first()
                    
                    # Si cambió el producto o almacén, verificamos contra el nuevo stock
                    if (movimiento.producto != old_producto or 
                        movimiento.almacen != old_almacen):
                        if stock and stock.cantidad < movimiento.cantidad:
                            messages.error(request, f'Stock insuficiente en nuevo almacén/producto. Disponible: {stock.cantidad}')
                            return render(request, 'movimientos/formulario.html', {
                                'form': form,
                                'modo': 'editar',
                                'titulo': f'Editar Movimiento: {movimiento.producto}',
                                'movimiento': movimiento
                            })
                    else:
                        # Ajustamos por la diferencia
                        diferencia = movimiento.cantidad - old_cantidad
                        if old_tipo == 'ENTRADA':
                            diferencia = -diferencia
                        
                        if stock and (stock.cantidad + diferencia) < 0:
                            messages.error(request, f'Stock insuficiente. Disponible: {stock.cantidad}')
                            return render(request, 'movimientos/formulario.html', {
                                'form': form,
                                'modo': 'editar',
                                'titulo': f'Editar Movimiento: {movimiento.producto}',
                                'movimiento': movimiento
                            })
                
                movimiento.save()
                messages.success(request, 'Movimiento actualizado exitosamente')
                return redirect('almacen:lista_movimientos')
            
            except Exception as e:
                messages.error(request, f'Error al actualizar movimiento: {str(e)}')
                return redirect('almacen:editar_movimiento', movimiento_id=movimiento_id)
    else:
        form = MovimientoInventarioForm(instance=movimiento)
    
    return render(request, 'movimientos/formulario.html', {
        'form': form,
        'modo': 'editar',
        'titulo': f'Editar Movimiento: {movimiento.producto}',
        'movimiento': movimiento
    })

@login_required
@transaction.atomic
def eliminar_movimiento(request, movimiento_id):
    if request.method == 'POST':
        try:
            movimiento = get_object_or_404(MovimientoInventario, pk=movimiento_id)
            
            # Verificamos si podemos revertir el stock
            if movimiento.tipo == 'SALIDA':
                stock = Stock.objects.filter(
                    producto=movimiento.producto,
                    almacen=movimiento.almacen
                ).first()
                
                if not stock:
                    messages.error(request, 'No existe registro de stock para este producto/almacén')
                    return redirect('almacen:lista_movimientos')
            
            movimiento.delete()
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            
            messages.success(request, 'Movimiento eliminado exitosamente')
            return redirect('almacen:lista_movimientos')
        
        except Exception as e:
            messages.error(request, f'Error al eliminar movimiento: {str(e)}')
            return redirect('almacen:lista_movimientos')
    
    return HttpResponseNotAllowed(['POST'])


@login_required
def lista_stock(request):
    stocks = Stock.objects.select_related('producto', 'almacen').order_by(
        'almacen__nombre', 'producto__nombre'
    )
    
    return render(request, 'stocks/lista.html', {
        'stocks': stocks,
        'titulo': 'Stock Actual'
    })














# almacen/views.py


from .services import convertir_producto, revertir_conversion


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import TipoConversion, ConversionProducto, RegistroConversion
from .forms import TipoConversionForm, EjecutarConversionForm
from .services import convertir_producto, revertir_conversion



@login_required
def menu_conversiones(request):
    return render(request, 'conversiones/menu_conversiones.html', {
        'titulo': 'Menú Conversiones'
    })

@login_required
def lista_tipos_conversion(request):
    tipos = TipoConversion.objects.all()
    return render(request, 'conversiones/lista_tipos.html', {
        'tipos': tipos,
        'titulo': 'Tipos de Conversión'
    })

@login_required
def crear_tipo_conversion(request):
    if request.method == 'POST':
        form = TipoConversionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de conversión creado exitosamente')
            return redirect('almacen:lista_tipos_conversion')
    else:
        form = TipoConversionForm()
    
    return render(request, 'conversiones/formulario_tipo.html', {
        'form': form,
        'titulo': 'Crear Tipo de Conversión'
    })


@login_required
def editar_tipo_conversion(request, tipo_conversion_id):
    tipo_conversion = get_object_or_404(TipoConversion, pk=tipo_conversion_id)
    
    if request.method == 'POST':
        form = TipoConversionForm(request.POST, instance=tipo_conversion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de conversión actualizado exitosamente')
            return redirect('almacen:lista_tipos_conversion')
    else:
        form = TipoConversionForm(instance=tipo_conversion)  # Cambiado de ConversionForm a TipoConversionForm
    
    return render(request, 'conversiones/formulario_tipo.html', {
        'form': form,
        'titulo': f'Editar Tipo de Conversión: {tipo_conversion.nombre}'  # Agregado .nombre para mejor visualización
    })



@login_required
def eliminar_tipo_conversion(request, tipo_conversion_id):
    if request.method== 'POST':
        tipo_conversion = get_object_or_404(TipoConversion, pk=tipo_conversion_id)
        tipo_conversion.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success':True})
        else:
            return redirect('almacen:lista_tipos_conversion')
    return HttpResponseNotAllowed(['POST'])


@login_required
def lista_conversiones(request):
    conversiones = ConversionProducto.objects.select_related(
        'tipo_conversion'
    ).prefetch_related(
        'componentes__producto__unidad_medida'
    ).all()
    
    return render(request, 'conversiones/lista_conversiones.html', {
        'conversiones': conversiones,
        'titulo': 'Conversiones Configuradas'
    })

@login_required
def crear_conversion(request):
    if request.method == 'POST':
        form = ConversionComplejaForm(request.POST)
        formset = ComponenteConversionFormSet(request.POST, instance=form.instance)
        
        if form.is_valid() and formset.is_valid():
            conversion = form.save()
            formset.instance = conversion
            formset.save()
            
            # Validar que haya al menos un origen y un destino
            componentes = conversion.componentes.all()
            if not componentes.filter(tipo='ORIGEN').exists() or not componentes.filter(tipo='DESTINO').exists():
                conversion.delete()
                messages.error(request, "Debe haber al menos un producto origen y un producto destino")
                return render(request, 'conversiones/formulario_conversion.html', {
                    'form': form,
                    'formset': formset,
                    'titulo': 'Crear Nueva Conversión'
                })
            
            messages.success(request, 'Conversión creada exitosamente')
            return redirect('almacen:lista_conversiones')
    else:
        form = ConversionComplejaForm()
        formset = ComponenteConversionFormSet(instance=ConversionProducto())
    
    return render(request, 'conversiones/formulario_conversion.html', {
        'form': form,
        'formset': formset,
        'titulo': 'Crear Nueva Conversión'
    })

@login_required
def editar_conversion(request, conversion_id):
    conversion = get_object_or_404(ConversionProducto, pk=conversion_id)
    
    if request.method == 'POST':
        form = ConversionComplejaForm(request.POST, instance=conversion)
        formset = ComponenteConversionFormSet(request.POST, instance=conversion)
        
        if form.is_valid() and formset.is_valid():
            conversion = form.save()
            formset.save()
            
            # Validar que haya al menos un origen y un destino
            componentes = conversion.componentes.all()
            if not componentes.filter(tipo='ORIGEN').exists() or not componentes.filter(tipo='DESTINO').exists():
                messages.error(request, "Debe haber al menos un producto origen y un producto destino")
                return render(request, 'conversiones/formulario_conversion.html', {
                    'form': form,
                    'formset': formset,
                    'titulo': f'Editar Conversión: {conversion}'
                })
            
            messages.success(request, 'Conversión actualizada exitosamente')
            return redirect('almacen:lista_conversiones')
    else:
        form = ConversionComplejaForm(instance=conversion)
        formset = ComponenteConversionFormSet(instance=conversion)
    
    return render(request, 'conversiones/formulario_conversion.html', {
        'form': form,
        'formset': formset,
        'titulo': f'Editar Conversión: {conversion}'
    })

@login_required
def activar_conversion(request, conversion_id):
    conversion = get_object_or_404(ConversionProducto, pk=conversion_id)
    conversion.activo = True
    conversion.save()
    messages.success(request, 'Conversión activada exitosamente')
    return redirect('almacen:lista_conversiones')

@login_required
def desactivar_conversion(request, conversion_id):
    conversion = get_object_or_404(ConversionProducto, pk=conversion_id)
    conversion.activo = False
    conversion.save()
    messages.success(request, 'Conversión desactivada exitosamente')
    return redirect('almacen:lista_conversiones')

@login_required
def ejecutar_conversion(request):
    if request.method == 'POST':
        form = EjecutarConversionForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                conversion = form.cleaned_data['conversion']
                almacen = form.cleaned_data['almacen']
                cantidad = form.cleaned_data['cantidad']
                
                # Validar stock para todos los componentes origen
                componentes_origen = conversion.componentes.filter(tipo='ORIGEN')
                for componente in componentes_origen:
                    stock = Stock.objects.filter(
                        producto=componente.producto,
                        almacen=almacen
                    ).first()
                    cantidad_necesaria = componente.cantidad * cantidad
                    
                    if not stock or stock.cantidad < cantidad_necesaria:
                        raise ValidationError(
                            f'Stock insuficiente de {componente.producto.nombre}. '
                            f'Necesario: {cantidad_necesaria}, Disponible: {stock.cantidad if stock else 0}'
                        )
                
                # Ejecutar la conversión
                with transaction.atomic():
                    # Restar productos origen
                    for componente in componentes_origen:
                        stock = Stock.objects.get(
                            producto=componente.producto,
                            almacen=almacen
                        )
                        stock.cantidad -= componente.cantidad * cantidad
                        stock.save()
                    
                    # Sumar productos destino
                    componentes_destino = conversion.componentes.filter(tipo='DESTINO')
                    for componente in componentes_destino:
                        stock, created = Stock.objects.get_or_create(
                            producto=componente.producto,
                            almacen=almacen,
                            defaults={'cantidad': 0}
                        )
                        stock.cantidad += componente.cantidad * cantidad
                        stock.save()
                    
                    # Registrar la conversión
                    RegistroConversion.objects.create(
                        conversion=conversion,
                        almacen=almacen,
                        cantidad_ejecuciones=cantidad,
                        usuario=request.user.perfil,
                        motivo=form.cleaned_data['motivo']
                    )
                
                messages.success(request, "Conversión realizada exitosamente")
                return redirect('almacen:historial_conversiones')
                
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = EjecutarConversionForm(user=request.user)
    
    return render(request, 'conversiones/ejecutar_conversion.html', {
        'form': form,
        'titulo': 'Ejecutar Conversión'
    })

@login_required
def historial_conversiones(request):
    registros = RegistroConversion.objects.select_related(
        'conversion', 'almacen', 'usuario__usuario'
    ).prefetch_related(
        'conversion__componentes__producto__unidad_medida'
    ).order_by('-fecha')
    
    # Filtros
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    if fecha_inicio:
        registros = registros.filter(fecha__gte=fecha_inicio)
    if fecha_fin:
        registros = registros.filter(fecha__lte=fecha_fin)
    
    return render(request, 'conversiones/historial_conversiones.html', {
        'registros': registros,
        'titulo': 'Historial de Conversiones'
    })

@login_required
def revertir_conversion_view(request, registro_id):
    registro = get_object_or_404(RegistroConversion, pk=registro_id)
    
    if registro.revertido:
        messages.error(request, "Esta conversión ya fue revertida")
        return redirect('almacen:historial_conversiones')
    
    try:
        with transaction.atomic():
            # Revertir: sumar productos origen y restar productos destino
            componentes = registro.conversion.componentes.all()
            
            for componente in componentes.filter(tipo='ORIGEN'):
                stock, _ = Stock.objects.get_or_create(
                    producto=componente.producto,
                    almacen=registro.almacen,
                    defaults={'cantidad': 0}
                )
                stock.cantidad += componente.cantidad * registro.cantidad_ejecuciones
                stock.save()
            
            for componente in componentes.filter(tipo='DESTINO'):
                stock = Stock.objects.get(
                    producto=componente.producto,
                    almacen=registro.almacen
                )
                stock.cantidad -= componente.cantidad * registro.cantidad_ejecuciones
                stock.save()
            
            # Registrar la reversión
            RegistroConversion.objects.create(
                conversion=registro.conversion,
                almacen=registro.almacen,
                cantidad_ejecuciones=registro.cantidad_ejecuciones,
                usuario=request.user.perfil,
                motivo=f"Reversión de #{registro.id}",
                relacion_reversion=registro
            )
            
            # Marcar como revertido
            registro.revertido = True
            registro.save()
            
            messages.success(request, "Conversión revertida exitosamente")
            
    except Exception as e:
        messages.error(request, f"Error al revertir: {str(e)}")
    
    return redirect('almacen:historial_conversiones')




from django.http import JsonResponse

@login_required
def api_detalle_conversion(request, pk):
    try:
        conversion = ConversionProducto.objects.get(pk=pk)
        almacen_id = request.GET.get('almacen_id')
        
        data = {
            'id': conversion.id,
            'nombre': conversion.nombre,
            'componentes_origen': [],
            'componentes_destino': [],
            'errores': []
        }
        
        # Componentes origen
        for componente in conversion.componentes.filter(tipo='ORIGEN'):
            item = {
                'producto_id': componente.producto.id,
                'producto_nombre': componente.producto.nombre,
                'cantidad': componente.cantidad,
                'unidad_medida': componente.producto.unidad_medida.abreviatura_sifen
            }
            
            if almacen_id:
                stock = Stock.objects.filter(
                    producto=componente.producto,
                    almacen_id=almacen_id
                ).first()
                item['stock_disponible'] = stock.cantidad if stock else 0
                
                # Validar stock
                cantidad_necesaria = componente.cantidad * int(request.GET.get('cantidad', 1))
                if item['stock_disponible'] < cantidad_necesaria:
                    data['errores'].append(
                        f'Stock insuficiente de {componente.producto.nombre}. '
                        f'Necesario: {cantidad_necesaria}, Disponible: {item["stock_disponible"]}'
                    )
            
            data['componentes_origen'].append(item)
        
        # Componentes destino
        for componente in conversion.componentes.filter(tipo='DESTINO'):
            data['componentes_destino'].append({
                'producto_id': componente.producto.id,
                'producto_nombre': componente.producto.nombre,
                'cantidad': componente.cantidad,
                'unidad_medida': componente.producto.unidad_medida.abreviatura_sifen
            })
        
        return JsonResponse(data)
        
    except ConversionProducto.DoesNotExist:
        return JsonResponse({'error': 'Conversión no encontrada'}, status=404)






# views.py
from django.db import transaction
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .forms import TrasladoForm, DetalleTrasladoFormSet
from .models import TrasladoProducto, DetalleTraslado


@login_required
def crear_traslado(request):
    if request.method == 'POST':
        form = TrasladoForm(request.POST, user=request.user)
        formset = DetalleTrasladoFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                traslado = form.save(commit=False)
                traslado.solicitante = request.user.perfil
                traslado.save()
                
                for detalle_form in formset:
                    if detalle_form.cleaned_data.get('producto'):
                        detalle = detalle_form.save(commit=False)
                        detalle.traslado = traslado
                        detalle.save()
                
                messages.success(request, 'Traslado creado exitosamente')
                return redirect('almacen:detalle_traslado', traslado_id=traslado.id)
    else:
        form = TrasladoForm(user=request.user)
        formset = DetalleTrasladoFormSet(queryset=DetalleTraslado.objects.none())
    
    return render(request, 'traslados/formulario.html', {
        'form': form,
        'formset': formset,
        'titulo': 'Nuevo Traslado'
    })

@login_required
def listar_traslados(request):
    traslados = TrasladoProducto.objects.select_related(
        'almacen_origen', 'almacen_destino', 'solicitante'
    ).order_by('-fecha_solicitud')
    
    return render(request, 'traslados/lista.html', {
        'traslados': traslados,
        'titulo': 'Historial de Traslados'
    })

@login_required
def detalle_traslado(request, traslado_id):
    traslado = get_object_or_404(TrasladoProducto.objects.select_related(
        'almacen_origen', 'almacen_destino', 'solicitante__usuario'
    ), pk=traslado_id)
    
    detalles = traslado.detalles.select_related('producto').all()
    
    # Precalcular stocks para cada detalle
    for detalle in detalles:
        detalle.stock_origen = Stock.objects.filter(
            producto=detalle.producto,
            almacen=traslado.almacen_origen
        ).first()
        detalle.stock_destino = Stock.objects.filter(
            producto=detalle.producto,
            almacen=traslado.almacen_destino
        ).first()
    
    return render(request, 'traslados/detalle.html', {
        'traslado': traslado,
        'detalles': detalles,
        'titulo': f'Traslado {traslado.referencia}'
    })

import logging
logger = logging.getLogger(__name__)


@login_required
@transaction.atomic
def procesar_traslado(request, traslado_id):
    traslado = get_object_or_404(TrasladoProducto.objects.select_related('almacen_origen', 'almacen_destino'), pk=traslado_id)
    
    if request.method == 'POST':
        try:
            # Validaciones de permiso y estado
            if request.user != traslado.almacen_origen.responsable:
                messages.error(request, 'No tienes permiso para procesar este traslado')
                return redirect('almacen:detalle_traslado', traslado_id=traslado.id)
            
            if traslado.estado != 'PENDIENTE':
                messages.error(request, 'El traslado no está en estado PENDIENTE')
                return redirect('almacen:detalle_traslado', traslado_id=traslado.id)
            
            # Primera pasada: validar todo antes de hacer cambios
            detalles_a_actualizar = []
            for detalle in traslado.detalles.all():
                cantidad_str = request.POST.get(f'detalle-{detalle.id}-cantidad_enviada', '0').strip()
                
                try:
                    cantidad = int(cantidad_str)
                except ValueError:
                    messages.error(request, f'Valor inválido para {detalle.producto.nombre}: "{cantidad_str}"')
                    return redirect('almacen:detalle_traslado', traslado_id=traslado.id)
                
                if cantidad <= 0:
                    messages.error(request, f'La cantidad para {detalle.producto.nombre} debe ser mayor a cero')
                    return redirect('almacen:detalle_traslado', traslado_id=traslado.id)
                
                if cantidad > detalle.cantidad_solicitada:
                    messages.error(request, 
                        f'No puedes enviar más de lo solicitado para {detalle.producto.nombre}. '
                        f'Solicitado: {detalle.cantidad_solicitada}'
                    )
                    return redirect('almacen:detalle_traslado', traslado_id=traslado.id)
                
                stock = Stock.objects.filter(
                    producto=detalle.producto,
                    almacen=traslado.almacen_origen
                ).first()
                
                if not stock:
                    messages.error(request, f'No existe stock para {detalle.producto.nombre} en el almacén de origen')
                    return redirect('almacen:detalle_traslado', traslado_id=traslado.id)
                
                if stock.cantidad < cantidad:
                    messages.error(request, 
                        f'Stock insuficiente de {detalle.producto.nombre}. '
                        f'Disponible: {stock.cantidad}, Solicitado: {cantidad}'
                    )
                    return redirect('almacen:detalle_traslado', traslado_id=traslado.id)
                
                detalles_a_actualizar.append((detalle, cantidad, stock))
            
            # Segunda pasada: realizar las actualizaciones
            with transaction.atomic():
                for detalle, cantidad, stock_origen in detalles_a_actualizar:
                    # Actualizar detalle
                    detalle.cantidad_enviada = cantidad
                    detalle.save()
                    
                    # Solo restar del almacén origen (eliminado el código que sumaba al destino)
                    stock_origen.cantidad -= cantidad
                    stock_origen.save()
                
                # Actualizar el traslado
                traslado.responsable = request.user.perfil
                traslado.estado = 'EN_PROCESO'
                traslado.save()
            
            messages.success(request, 'Traslado procesado exitosamente')
            return redirect('almacen:detalle_traslado', traslado_id=traslado.id)
        
        except Exception as e:
            messages.error(request, f'Error al procesar traslado: {str(e)}')
            return redirect('almacen:detalle_traslado', traslado_id=traslado.id)
    
    return redirect('almacen:detalle_traslado', traslado_id=traslado.id)



@login_required
@transaction.atomic
def recibir_traslado(request, traslado_id):
    traslado = get_object_or_404(TrasladoProducto, pk=traslado_id)
    
    if request.method == 'POST':
        try:
            # Validaciones de permiso y estado
            if request.user != traslado.almacen_destino.responsable:
                messages.error(request, 'No tienes permiso para recibir este traslado')
                return redirect('almacen:detalle_traslado', traslado_id=traslado.id)
            
            if traslado.estado != 'EN_PROCESO':
                messages.error(request, 'El traslado no está en estado EN_PROCESO')
                return redirect('almacen:detalle_traslado', traslado_id=traslado.id)
            
            # Procesar cada detalle
            for detalle in traslado.detalles.all():
                cantidad_str = request.POST.get(f'detalle-{detalle.id}-cantidad_recibida', '0')
                
                try:
                    cantidad = int(cantidad_str)
                except ValueError:
                    cantidad = 0
                
                # Validaciones
                if cantidad <= 0:
                    messages.error(request, f'La cantidad para {detalle.producto.nombre} debe ser mayor a cero')
                    return redirect('almacen:detalle_traslado', traslado_id=traslado.id)
                
                if cantidad > detalle.cantidad_enviada:
                    messages.error(request, 
                        f'No puedes recibir más de lo enviado para {detalle.producto.nombre}. '
                        f'Enviado: {detalle.cantidad_enviada}'
                    )
                    return redirect('almacen:detalle_traslado', traslado_id=traslado.id)
                
                # Actualizar detalle
                detalle.cantidad_recibida = cantidad
                detalle.save()
            
            # Actualizar el traslado
            traslado.estado = 'COMPLETADO'
            traslado.fecha_completado = timezone.now()
            traslado.save()
            
            messages.success(request, 'Traslado recibido exitosamente')
            return redirect('almacen:detalle_traslado', traslado_id=traslado.id)
        
        except Exception as e:
            messages.error(request, f'Error al recibir traslado: {str(e)}')
            return redirect('almacen:detalle_traslado', traslado_id=traslado.id)
    
    return redirect('almacen:detalle_traslado', traslado_id=traslado.id)





def lista_inventarios():
    pass

def lista_reportes():
    pass


