from django.contrib import messages
from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from .models import Producto, Categoria, UnidadMedida,MovimientoInventario, Almacen, Stock
from .forms import ProductoForm, CategoriaForm, UnidadMedidaForm, MovimientoInventarioForm, AlmacenForm

from django.db import transaction


def lista_productos(request):
    producto = Producto.objects.all()
    return render(request, 'productos/lista.html', {'productos': producto})

def lista_categorias(request):
    categoria = Categoria.objects.all()
    return render(request, 'categorias/lista.html', {'categorias': categoria})

def lista_unidades_medidas(request):
    unidad_medida= UnidadMedida.objects.all()
    return render(request,'unidades_medidas/lista.html', {'unidades_medidas': unidad_medida})

def lista_almacenes(request):
    almacenes = Almacen.objects.all()
    return render(request, 'almacenes/lista.html', {
        'almacenes': almacenes,
        'titulo': 'Lista de Almacenes'
    })

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

def eliminar_producto(request, producto_id):
    if request.method== 'POST':
        producto= get_object_or_404(Producto, pk= producto_id)
        producto.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success':True})
        else:
            return redirect('almacen:lista_productos')
    return HttpResponseNotAllowed(['POST'])

def eliminar_categoria(request, categoria_id):
    if request.method == 'POST':
        categoria= get_object_or_404(Categoria, pk=categoria_id)
        categoria.delete()
        if request.headers.get('x-requested-with')== 'XMLHttpRequest':
            return JsonResponse({'success':True})
        else:
            return redirect('almacen:lista_categorias')
    return HttpResponseNotAllowed(['POST'])

def eliminar_unidad_medida(request, unidad_medida_id):
    if request.method == 'POST':
        unidad_medida = get_object_or_404(UnidadMedida, pk= unidad_medida_id)
        unidad_medida.delete()
        if request.headers.get('x-requested-with')== 'XMLHttpRequest':
            return JsonResponse({'success':True})
        else:
            return redirect('almacen:lista_unidades_medidas')
    return HttpResponseNotAllowed(['POST'])

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

def eliminar_almacen(request, almacen_id):
    if request.method == 'POST':
        almacen = get_object_or_404(Almacen, pk=almacen_id)
        almacen.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        messages.success(request, 'Almacén eliminado exitosamente')
        return redirect('almacen:lista_almacenes')
    return HttpResponseNotAllowed(['POST'])

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

def lista_movimientos(request):
    movimientos = MovimientoInventario.objects.select_related(
        'producto', 'almacen', 'usuario'
    ).order_by('-fecha')
    
    return render(request, 'movimientos/lista.html', {
        'movimientos': movimientos,
        'titulo': 'Historial de Movimientos'
    })

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

def lista_stock(request):
    stocks = Stock.objects.select_related('producto', 'almacen').order_by(
        'almacen__nombre', 'producto__nombre'
    )
    
    return render(request, 'stocks/lista.html', {
        'stocks': stocks,
        'titulo': 'Stock Actual'
    })

def lista_inventarios():
    pass

def lista_reportes():
    pass


