from django.db import models
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from usuarios.models import PerfilUsuario
from empresa.models import PuntoExpedicion

class Caja(models.Model):
    ESTADO_CHOICES = [
        ('ABIERTA', 'Abierta'),
        ('CERRADA', 'Cerrada'),
    ]
    punto_expedicion = models.OneToOneField(PuntoExpedicion, on_delete=models.PROTECT,related_name='caja')
    nombre = models.CharField(max_length=100, unique=True)
    saldo_inicial = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo_actual = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='CERRADA')
    responsable = models.ForeignKey(PerfilUsuario, on_delete=models.PROTECT, related_name='cajas_responsable')
    fecha_apertura = models.DateTimeField(null=True, blank=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Caja'
        verbose_name_plural = 'Cajas'
        ordering = ['-fecha_apertura']
        permissions = [
            ('puede_abrir_caja', 'Puede abrir cajas'),
            ('puede_cerrar_caja', 'Puede cerrar cajas'),
        ]

    def __str__(self):
        return f"{self.nombre} - {self.responsable.usuario.get_full_name()}"

    def clean(self):
        if self.estado == 'ABIERTA' and not self.fecha_apertura:
            self.fecha_apertura = timezone.now()
        if self.estado == 'CERRADA' and not self.fecha_cierre:
            self.fecha_cierre = timezone.now()

    @property
    def sesion_activa(self):
        return self.sesiones.filter(estado='ABIERTA').first()

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
        
        # Crear nueva sesión
        SesionCaja.objects.create(
            caja=self,
            responsable=responsable,
            saldo_inicial=saldo_inicial
        )

    @transaction.atomic
    def cerrar(self, saldo_final=None):
        if self.estado == 'CERRADA':
            raise ValidationError('La caja ya está cerrada')
        
        sesion = self.sesion_activa
        if sesion:
            saldo_final = saldo_final or self.saldo_actual
            sesion.cerrar(saldo_final)
        
        self.estado = 'CERRADA'
        self.fecha_cierre = timezone.now()
        self.save()

class SesionCaja(models.Model):
    caja = models.ForeignKey(Caja, on_delete=models.PROTECT, related_name='sesiones')
    responsable = models.ForeignKey(PerfilUsuario, on_delete=models.PROTECT, related_name='sesiones_caja')
    saldo_inicial = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_final = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    fecha_apertura = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    observaciones = models.TextField(blank=True)
    estado = models.CharField(max_length=10, choices=[('ABIERTA', 'Abierta'), ('CERRADA', 'Cerrada')], default='ABIERTA')

    class Meta:
        verbose_name = 'Sesión de Caja'
        verbose_name_plural = 'Sesiones de Caja'
        ordering = ['-fecha_apertura']
        indexes = [
            models.Index(fields=['estado', 'fecha_apertura']),
        ]

    def __str__(self):
        return f"Sesión {self.id} - {self.caja.nombre} ({self.get_estado_display()})"

    @property
    def movimientos(self):
        return MovimientoCaja.objects.filter(
            caja=self.caja,
            fecha__gte=self.fecha_apertura,
            fecha__lte=self.fecha_cierre if self.fecha_cierre else timezone.now()
        )


    @property
    def saldo_teorico(self):
        # Convertir el RelatedManager a una lista evaluando la consulta
        movimientos = list(self.movimientos.all())
        total = self.saldo_inicial
        for movimiento in movimientos:
            if movimiento.tipo == 'INGRESO':
                total += movimiento.monto
            else:
                total -= movimiento.monto
        return total

    @property
    def diferencia(self):
        if self.saldo_final is not None:
            try:
                return self.saldo_final - self.saldo_teorico
            except (TypeError, AttributeError):
                return 0
        return None




    @transaction.atomic
    def cerrar(self, saldo_final, observaciones=''):
        if self.estado == 'CERRADA':
            raise ValidationError('Esta sesión ya está cerrada')
        
        self.saldo_final = saldo_final
        self.fecha_cierre = timezone.now()
        self.observaciones = observaciones
        self.estado = 'CERRADA'
        self.save()
        
        # Actualizar saldo de la caja padre
        self.caja.saldo_actual = saldo_final
        self.caja.save()

class MovimientoCaja(models.Model):
    TIPO_CHOICES = [
        ('INGRESO', 'Ingreso'),
        ('EGRESO', 'Egreso'),
    ]

    caja = models.ForeignKey(Caja, on_delete=models.PROTECT, related_name='movimientos')
    sesion = models.ForeignKey(SesionCaja, on_delete=models.PROTECT, related_name='movimientos', null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)
    responsable = models.ForeignKey(PerfilUsuario, on_delete=models.PROTECT, related_name='movimientos_registrados')
    descripcion = models.TextField()
    venta = models.ForeignKey('ventas.Venta', on_delete=models.SET_NULL, null=True, blank=True)
    nota_credito = models.ForeignKey(
        'ventas.NotaCredito', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='movimientos_caja'
    )
    compra = models.ForeignKey('compras.OrdenCompra', on_delete=models.SET_NULL, null=True, blank=True)
    comprobante = models.CharField(max_length=50, blank=True, unique=True)
    imagen_comprobante = models.ImageField(upload_to='comprobantes/caja/', null=True, blank=True)

    class Meta:
        verbose_name = 'Movimiento de Caja'
        verbose_name_plural = 'Movimientos de Caja'
        ordering = ['-fecha']
        constraints = [
            models.CheckConstraint(
                check=models.Q(monto__gt=0),
                name='monto_positivo'
            )
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - ${self.monto} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"

    def clean(self):
        if self.monto <= 0:
            raise ValidationError('El monto debe ser positivo')
        
        # Solo intentar asignar sesión si la caja ya está asignada
        if hasattr(self, 'caja') and not self.sesion and self.caja.sesion_activa:
            self.sesion = self.caja.sesion_activa

    def save(self, *args, **kwargs):
        """
        Guarda el movimiento y actualiza el saldo de la caja.
        Asigna automáticamente la sesión activa si existe.
        """
        with transaction.atomic():
            # Primero validamos (esto incluirá la asignación de sesión si es posible)
            self.full_clean()
            
            # Guardamos el movimiento
            super().save(*args, **kwargs)
            
            # Actualizar saldo de la caja solo si está asignada
            if hasattr(self, 'caja'):
                if self.tipo == 'INGRESO':
                    self.caja.saldo_actual += self.monto
                else:
                    self.caja.saldo_actual -= self.monto
                self.caja.save()