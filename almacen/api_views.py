# almacen/api_views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Producto
from .serializers import ProductoSerializer

@api_view(['GET'])
def buscar_producto(request):
    codigo = request.GET.get('codigo', '').strip()
    print(f"Código recibido: '{codigo}'")  # Para depuración
    
    if not codigo:
        return Response({'error': 'Código requerido'}, status=400)
    
    try:
        # Agrega insensitive lookup si es necesario
        producto = Producto.objects.get(codigo__iexact=codigo)
        print(f"Producto encontrado: {producto}")  # Para depuración
        serializer = ProductoSerializer(producto)
        return Response(serializer.data)
    except Producto.DoesNotExist:
        print("Producto no encontrado")  # Para depuración
        return Response({'error': 'Producto no encontrado'}, status=404)
    except Exception as e:
        print(f"Error inesperado: {str(e)}")  # Para depuración
        return Response({'error': 'Error en el servidor'}, status=500)

# almacen/api_views.py

@api_view(['GET'])
def obtener_producto_por_id(request, pk):
    try:
        producto = Producto.objects.get(pk=pk)
        serializer = ProductoSerializer(producto)
        return Response(serializer.data)
    except Producto.DoesNotExist:
        return Response({'error': 'Producto no encontrado'}, status=404)
