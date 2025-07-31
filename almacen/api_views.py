from django.db import models
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Producto, Servicio, Almacen
from .serializers import ProductoSerializer, ServicioSerializer
from django.db.models import Q

@api_view(['GET'])
def buscar_producto(request):
    codigo = request.GET.get('codigo', '').strip()
    
    if not codigo:
        return Response({'error': 'Código requerido'}, status=400)
    
    try:
        producto = Producto.objects.get(codigo__iexact=codigo)
        serializer = ProductoSerializer(producto)
        return Response(serializer.data)
    except Producto.DoesNotExist:
        return Response({'error': 'Producto no encontrado'}, status=404)
    except Exception as e:
        return Response({'error': 'Error en el servidor'}, status=500)

@api_view(['GET'])
def obtener_producto_por_id(request, pk):
    try:
        producto = Producto.objects.get(pk=pk)
        serializer = ProductoSerializer(producto)
        return Response(serializer.data)
    except Producto.DoesNotExist:
        return Response({'error': 'Producto no encontrado'}, status=404)

@api_view(['GET'])
def buscar_servicio(request):
    query = request.GET.get('q', '').strip()
    
    if not query:
        return Response({'error': 'Parámetro de búsqueda requerido'}, status=400)
    
    try:
        # Buscar por código o nombre (insensitive)
        servicio = Servicio.objects.filter(
            models.Q(codigo__iexact=query) | 
            models.Q(nombre__icontains=query)
        ).first()
        
        if not servicio:
            return Response({'error': 'Servicio no encontrado'}, status=404)
            
        serializer = ServicioSerializer(servicio)
        return Response(serializer.data)
    except Exception as e:
        return Response({'error': f'Error en el servidor: {str(e)}'}, status=500)

@api_view(['GET'])
def obtener_servicio_por_id(request, pk):
    try:
        servicio = Servicio.objects.get(pk=pk)
        serializer = ServicioSerializer(servicio)
        return Response({
            **serializer.data,
            'tipo_servicio': servicio.tipo,
            'necesita_inventario': servicio.necesita_inventario
        })
    except Servicio.DoesNotExist:
        return Response({'error': 'Servicio no encontrado'}, status=404)

@api_view(['GET'])
def buscar_producto_servicio(request):
    """
    API unificada para buscar tanto productos como servicios
    """
    query = request.GET.get('q', '').strip()
    
    if not query:
        return Response({'error': 'Parámetro de búsqueda requerido'}, status=400)
    
    try:
        # Buscar productos
        productos = Producto.objects.filter(
            Q(codigo__iexact=query) | 
            Q(nombre__icontains=query),
            activo=True
        )[:5]  # Limitar resultados
        
        # Buscar servicios
        servicios = Servicio.objects.filter(
            Q(codigo__iexact=query) | 
            Q(nombre__icontains=query),
            activo=True
        )[:5]  # Limitar resultados
        
        producto_serializer = ProductoSerializer(productos, many=True)
        servicio_serializer = ServicioSerializer(servicios, many=True)
        
        return Response({
            'productos': producto_serializer.data,
            'servicios': servicio_serializer.data
        })
    except Exception as e:
        return Response({'error': f'Error en el servidor: {str(e)}'}, status=500)


@api_view(['GET'])
def obtener_almacen_principal(request):
    try:
        almacen = Almacen.objects.filter(es_principal=True).first()
        if not almacen:
            return Response({'error': 'No hay almacén principal configurado'}, status=404)
        
        return Response({
            'id': almacen.id,
            'nombre': almacen.nombre,
            'sucursal': almacen.sucursal.nombre if almacen.sucursal else ''
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)