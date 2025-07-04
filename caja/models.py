from django.db import models
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from usuarios.models import PerfilUsuario

class Caja(models.Model):
    ESTADO_CHOICES = [
        ('ABIERTA', 'Abierta'),
        ('CERRADA', 'Cerrada'),
    ]

    nombre = models.CharField(max_length=100, unique=True)
    saldo_inicial = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo_actual = models.DecimalField(max_digits=12, decimal_places=2,default=0)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='CERRADA')
    responsable = models.ForeignKey(PerfilUsuario, on_delete=models.PROTECT)
    fecha_apertura = models.DateTimeField(null=True, blank=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Caja'
        verbose_name_plural = 'Cajas'
        ordering = ['-fecha_apertura']

    def __str__(self):
        return f"{self.nombre} - {self.responsable.usuario.username}"

    def clean(self):
        if self.estado == 'ABIERTA' and not self.fecha_apertura:
            self.fecha_apertura = timezone.now()
        if self.estado == 'CERRADA' and not self.fecha_cierre:
            self.fecha_cierre = timezone.now()

    @transaction.atomic
    def abrir(self, responsable, saldo_inicial):
        if self.estado == 'ABIERTA':
            raise ValidationError('La caja ya está abierta')
        
        self.responsable = responsable
        self.saldo_inicial = saldo_inicial
        self.saldo_actual = saldo_inicial
        self.estado = 'ABIERTA'
        self.fecha_apertura = timezone.now()
        self.save()

    @transaction.atomic
    def cerrar(self):
        if self.estado == 'CERRADA':
            raise ValidationError('La caja ya está cerrada')
        
        self.estado = 'CERRADA'
        self.fecha_cierre = timezone.now()
        self.save()

class MovimientoCaja(models.Model):
    TIPO_CHOICES = [
        ('INGRESO', 'Ingreso'),
        ('EGRESO', 'Egreso'),
    ]

    caja = models.ForeignKey(Caja, on_delete=models.PROTECT, related_name='movimientos')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)
    responsable = models.ForeignKey(PerfilUsuario, on_delete=models.PROTECT)
    descripcion = models.TextField()
    venta = models.ForeignKey('ventas.Venta', on_delete=models.SET_NULL, null=True, blank=True)  # Usa string
    compra = models.ForeignKey('compras.OrdenCompra', on_delete=models.SET_NULL, null=True, blank=True)  # Usa string
    comprobante = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = 'Movimiento de Caja'
        verbose_name_plural = 'Movimientos de Caja'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.monto} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"

    def clean(self):
        if self.tipo == 'INGRESO' and self.monto <= 0:
            raise ValidationError('El monto de ingreso debe ser positivo')
        if self.tipo == 'EGRESO' and self.monto <= 0:
            raise ValidationError('El monto de egreso debe ser positivo')

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            
            # Actualizar saldo de la caja
            if self.tipo == 'INGRESO':
                self.caja.saldo_actual += self.monto
            else:
                self.caja.saldo_actual -= self.monto
                
            self.caja.save()
