from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.forms import ValidationError
from django.utils import timezone
from .models import DetalleTraslado, MovimientoInventario,Stock

@receiver(post_save, sender=DetalleTraslado)
def actualizar_estado_traslado(sender, instance, **kwargs):
    traslado = instance.traslado
    detalles = traslado.detalles.all()
    
    # Solo actualizar si hay cambios en cantidades enviadas/recibidas
    if any(d.has_changed() for d in detalles):
        # Estado EN_PROCESO cuando todo está enviado pero no recibido
        if all(d.cantidad_enviada == d.cantidad_solicitada for d in detalles):
            traslado.estado = 'EN_PROCESO'
            traslado.save()
        
        # Estado COMPLETADO cuando todo está recibido
        if all(d.cantidad_recibida == d.cantidad_enviada for d in detalles if d.cantidad_enviada > 0):
            traslado.estado = 'COMPLETADO'
            traslado.fecha_completado = timezone.now()
            traslado.save()

@receiver(post_save, sender=DetalleTraslado)
def registrar_movimiento_entrada(sender, instance, **kwargs):
    # Solo registrar entrada si el traslado está COMPLETADO
    if (instance.cantidad_recibida > 0 and 
        instance.has_changed('cantidad_recibida') and 
        instance.traslado.estado == 'COMPLETADO'):
        
        # Verificar si ya existe un movimiento para esta recepción
        existe_movimiento = MovimientoInventario.objects.filter(
            producto=instance.producto,
            almacen=instance.traslado.almacen_destino,
            motivo=f"Traslado {instance.traslado.referencia} desde {instance.traslado.almacen_origen}",
            tipo='ENTRADA'
        ).exists()
        
        if not existe_movimiento:
            # Crear el movimiento de entrada
            MovimientoInventario.objects.create(
                producto=instance.producto,
                almacen=instance.traslado.almacen_destino,
                cantidad=instance.cantidad_recibida,
                tipo='ENTRADA',
                usuario=instance.traslado.responsable or instance.traslado.solicitante,
                motivo=f"Traslado {instance.traslado.referencia} desde {instance.traslado.almacen_origen}"
            )
            
            # Actualizar el stock de destino
            stock_destino, created = Stock.objects.get_or_create(
                producto=instance.producto,
                almacen=instance.traslado.almacen_destino,
                defaults={'cantidad': 0}
            )
            stock_destino.cantidad += instance.cantidad_recibida
            stock_destino.save()

@receiver(post_save, sender=DetalleTraslado)
def registrar_movimiento_entrada(sender, instance, **kwargs):
    if instance.cantidad_recibida > 0 and instance.has_changed('cantidad_recibida'):
        MovimientoInventario.objects.create(
            producto=instance.producto,
            almacen=instance.traslado.almacen_destino,
            cantidad=instance.cantidad_recibida,
            tipo='ENTRADA',
            usuario=instance.traslado.responsable or instance.traslado.solicitante,
            motivo=f"Traslado {instance.traslado.referencia} desde {instance.traslado.almacen_origen}"
        )