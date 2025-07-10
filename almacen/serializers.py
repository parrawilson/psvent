# almacen/serializers.py
from rest_framework import serializers
from .models import Producto

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = ['id', 'codigo', 'nombre', 'precio_minorista', 'precio_mayorista', 'tasa_iva', 'descripcion']