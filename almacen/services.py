# almacen/services.py
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import ConversionProducto, Stock, RegistroConversion, Almacen

@transaction.atomic
def convertir_producto(conversion_id, almacen_id, cantidad, usuario, motivo=""):
    """
    Ejecuta una conversión entre productos (ensamblaje/desensamblaje)
    
    Args:
        conversion_id: ID de la ConversionProducto configurada
        almacen_id: ID del almacén donde se realiza
        cantidad: Unidades a convertir
        usuario: Usuario que realiza la acción
        motivo: Justificación opcional
    """
    conversion = ConversionProducto.objects.get(pk=conversion_id)
    almacen = Almacen.objects.get(pk=almacen_id)
    
    # Verificación de stock
    stock_origen = Stock.objects.get(
        producto=conversion.producto_origen,
        almacen=almacen
    )
    if stock_origen.cantidad < cantidad:
        raise ValidationError(
            f"Stock insuficiente de {conversion.producto_origen.nombre}. "
            f"Necesario: {cantidad}, Disponible: {stock_origen.cantidad}"
        )
    
    # Cálculo de resultados
    cantidad_destino = cantidad * conversion.cantidad_destino
    
    # Actualización de stock
    stock_origen.cantidad -= cantidad
    stock_origen.save()
    
    stock_destino, _ = Stock.objects.get_or_create(
        producto=conversion.producto_destino,
        almacen=almacen,
        defaults={'cantidad': 0}
    )
    stock_destino.cantidad += cantidad_destino
    stock_destino.save()
    
    # Registro auditoría
    registro = RegistroConversion.objects.create(
        tipo_conversion=conversion.tipo_conversion,
        producto_origen=conversion.producto_origen,
        producto_destino=conversion.producto_destino,
        cantidad_origen=cantidad,
        cantidad_destino=cantidad_destino,
        almacen=almacen,
        usuario=usuario,
        motivo=motivo
    )
    
    return registro



# almacen/services.py (continuación)
@transaction.atomic
def revertir_conversion(registro_id, usuario, motivo=""):
    """
    Revierte una conversión registrada previamente
    
    Args:
        registro_id: ID del RegistroConversion a revertir
        usuario: Usuario que realiza la reversión
        motivo: Justificación opcional
    """
    original = RegistroConversion.objects.get(pk=registro_id)
    
    if original.revertido:
        raise ValidationError("Esta conversión ya fue revertida")
    
    # Crear registro inverso
    registro = RegistroConversion.objects.create(
        tipo_conversion=original.tipo_conversion,
        producto_origen=original.producto_destino,
        producto_destino=original.producto_origen,
        cantidad_origen=original.cantidad_destino,
        cantidad_destino=original.cantidad_origen,
        almacen=original.almacen,
        usuario=usuario,
        motivo=f"Reversión de #{original.id}: {motivo}",
        relacion_reversion=original
    )
    
    # Revertir stocks
    stock_origen = Stock.objects.get(
        producto=original.producto_origen,
        almacen=original.almacen
    )
    stock_origen.cantidad += original.cantidad_origen
    stock_origen.save()
    
    stock_destino = Stock.objects.get(
        producto=original.producto_destino,
        almacen=original.almacen
    )
    stock_destino.cantidad -= original.cantidad_destino
    stock_destino.save()
    
    # Marcar como revertido
    original.revertido = True
    original.save()
    
    return registro