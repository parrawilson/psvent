# models.py
from datetime import timezone
from django.db import models
from ventas.models import Venta

class DocumentoElectronico(models.Model):
    ESTADOS = (
        ('NO_GENERADO', 'No generado'),
        ('BORRADOR', 'Borrador (XML generado)'),
        ('VALIDADO', 'Validado contra XSD'),
        ('ENVIADO', 'Enviado al SET'),
        ('ACEPTADO', 'Aceptado por SET'),
        ('ERROR', 'Error'),
    )

    venta = models.OneToOneField(Venta, on_delete=models.CASCADE, related_name='documento_electronico')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='NO_GENERADO')
    xml_generado = models.TextField(null=True, blank=True)
    xml_firmado = models.TextField(null=True, blank=True)
    respuesta_set = models.JSONField(null=True, blank=True)
    codigo_set = models.CharField(max_length=50, null=True, blank=True)
    qr_url = models.URLField(max_length=500, null=True, blank=True)  # Cambiado a URLField
    pdf = models.BinaryField(null=True, blank=True)  # Añadido para almacenar PDF
    fecha_envio = models.DateTimeField(null=True, blank=True)
    fecha_aceptacion = models.DateTimeField(null=True, blank=True)  # Añadido
    errores = models.TextField(null=True, blank=True)
    intentos = models.PositiveSmallIntegerField(default=0)  # Añadido para reintentos

    class Meta:
        verbose_name = 'Documento Electrónico'
        verbose_name_plural = 'Documentos Electrónicos'
        indexes = [
            models.Index(fields=['estado']),
            models.Index(fields=['codigo_set']),
        ]

    def __str__(self):
        return f"DE-{self.venta.numero} ({self.get_estado_display()})"

    def marcar_como_enviado(self):
        self.estado = 'ENVIADO'
        self.fecha_envio = timezone.now()
        self.intentos += 1
        self.save()

    def marcar_como_aceptado(self, respuesta):
        self.estado = 'ACEPTADO'
        self.respuesta_set = respuesta
        self.fecha_aceptacion = timezone.now()
        self.save()

    def marcar_como_error(self, error):
        self.estado = 'ERROR'
        self.errores = str(error)
        self.save()