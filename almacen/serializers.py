# almacen/serializers.py
from rest_framework import serializers
from .models import Producto, Servicio

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = ['id', 'codigo', 'nombre', 'precio_minorista', 'precio_mayorista', 'tasa_iva', 'stock_minimo']

class ServicioSerializer(serializers.ModelSerializer):
    necesita_inventario = serializers.SerializerMethodField()
    
    class Meta:
        model = Servicio
        fields = ['id', 'codigo', 'nombre', 'descripcion', 'tipo', 'precio', 
                 'tasa_iva', 'duracion_estimada', 'necesita_inventario']
    
    def get_necesita_inventario(self, obj):
        return obj.tipo == 'COMPUESTO' and obj.componentes.exists()