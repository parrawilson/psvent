
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from ventas.models import Venta
from .models import DocumentoElectronico
from .services.sifen import SifenService  # Esta es la línea corregida

@receiver(post_save, sender=Venta)
def manejar_documento_electronico(sender, instance, created, **kwargs):
"""    
    #Gestiona automáticamente el documento electrónico cuando:
    #- La venta se marca como FINALIZADA
    #- El cliente requiere factura electrónica
"""   
    if instance.estado == 'FINALIZADA':
        cliente_valido = (
            instance.cliente and 
            instance.cliente.tipo_documento in ['RUC', 'Cédula']
        )
        
        if cliente_valido:
            doc, created = DocumentoElectronico.objects.get_or_create(
                venta=instance,
                defaults={'estado': 'NO_GENERADO'}
            )
            
            if doc.estado == 'NO_GENERADO':
                SifenService.generar_documento(instance, firmar=True)
"""