
from django.db import models
from django.db import transaction
from django.core.exceptions import ValidationError
from almacen.models import Producto, MovimientoInventario, Almacen
from usuarios.models import PerfilUsuario
from django.db.models.signals import post_save
from django.dispatch import receiver
from caja.models import MovimientoCaja
from django.utils import timezone

class Proveedor(models.Model):
    ruc = models.CharField(max_length=20, unique=True)
    dv = models.CharField(max_length=2,blank=True)
    razon_social = models.CharField(max_length=200)
    direccion = models.TextField(blank=True)
    telefono = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.razon_social

class OrdenCompra(models.Model):
    ESTADO_CHOICES = [
        ('BORRADOR', 'Borrador'),
        ('APROBADA', 'Aprobada'),
        ('RECIBIDA', 'Recibida'),
        ('CANCELADA', 'Cancelada'),
        ('PAGADA', 'Pagada'),
    ]
    TIPO_DOCUMENTO = [
        ('F','FACTURA'),
        ('T','TICKET'),
    ]
    TIPO_CONDICION =[
        ('1','CONTADO'),
        ('2','CREDITO'),
    ]

 
    numero = models.CharField(max_length=20, unique=True)
    tipo_documento = models.CharField(max_length=20,choices=TIPO_DOCUMENTO, default='F')
    numero_documento = models.CharField(max_length=15,blank=True)
    timbrado = models.CharField(max_length=8,blank=True)
    condicion = models.CharField(max_length=20,choices=TIPO_CONDICION, null=True, blank=True)
    plazo_dias = models.PositiveIntegerField(
        default=0,
        help_text="Plazo en días para pagos a crédito"
    )
    fecha_vencimiento = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha de vencimiento para pagos a crédito"
    )
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT)
    fecha = models.DateField(auto_now_add=True)
    fecha_entrega = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='BORRADOR')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    creado_por = models.ForeignKey(PerfilUsuario, on_delete=models.PROTECT, related_name='ordenes_compra')
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    notas = models.TextField(blank=True)

    caja = models.ForeignKey('caja.Caja', on_delete=models.PROTECT, null=True, blank=True)
    movimiento_caja = models.ForeignKey('caja.MovimientoCaja', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Orden de Compra'
        verbose_name_plural = 'Órdenes de Compra'

    def __str__(self):
        return f"OC-{self.numero}"

    def calcular_totales(self):
        """Calcula los totales basados en los detalles"""
        detalles = self.detalles.all()
        self.subtotal = sum(detalle.subtotal for detalle in detalles)
        self.total = self.subtotal 
        self.save()

    def aprobar(self, usuario):
        """Aprueba la orden de compra"""
        if self.estado == 'BORRADOR':
            self.estado = 'APROBADA'
            self.save()
            # Aquí podrías agregar notificaciones o historial

    @transaction.atomic
    def recibir(self, usuario, almacen, tipo_pago, tipo_documento, numero_documento, timbrado,condicion, caja=None,plazo_dias=0):
        """Marca la orden como recibida y actualiza inventario"""
        if self.estado != 'APROBADA':
            raise ValidationError('Solo se pueden recibir órdenes aprobadas')
        
        # Asegurarnos que plazo_dias es un entero
        try:
            plazo_dias = int(plazo_dias)
        except (ValueError, TypeError):
            plazo_dias = 0

        # Actualizar condición y plazo
        self.timbrado = timbrado
        self.condicion = condicion
        self.plazo_dias = plazo_dias
        self.numero_documento=numero_documento
        self.tipo_documento=tipo_documento

        if condicion == '2':  # Crédito
            self.fecha_vencimiento = (timezone.now() + timezone.timedelta(days=int(plazo_dias))).date()
        
        with transaction.atomic():
            # Registrar recepción
            recepcion = RecepcionCompra.objects.create(
                orden=self,
                recibido_por=usuario,
                almacen=almacen,
                tipo_pago=tipo_pago
            )
            
            # Registrar movimiento de caja si se especificó
            movimiento = None

            if condicion == '1' and tipo_pago == 'EFECTIVO' and caja and caja.estado == 'ABIERTA':
                movimiento = MovimientoCaja.objects.create(
                    caja=caja,
                    tipo='EGRESO',
                    monto=self.total,
                    responsable=usuario,
                    descripcion=f"Compra {self.numero}",
                    compra=self,
                    comprobante=f"OC-{self.numero}"
                )
            
            # Procesar cada detalle
            for detalle in self.detalles.all():
                detalle.cantidad_recibida = detalle.cantidad
                detalle.recibido = True
                detalle.save()
                
                # Actualizar precio de compra
                if detalle.producto.precio_compra != detalle.precio_unitario:
                    detalle.producto.precio_compra = detalle.precio_unitario
                    detalle.producto.save()
                
                # Registrar movimiento de inventario
                MovimientoInventario.objects.create(
                    producto=detalle.producto,
                    almacen=almacen,
                    cantidad=detalle.cantidad,
                    tipo='ENTRADA',
                    usuario=usuario,
                    motivo=f"Recepción de OC-{self.numero}"
                )
            
            # Actualizar estado de la orden
            self.estado = 'RECIBIDA'
            self.caja = caja if condicion == '1' else None  # Solo asignar caja si es contado
            self.movimiento_caja = movimiento
            self.save()

class DetalleOrdenCompra(models.Model):
    orden = models.ForeignKey(OrdenCompra, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    recibido = models.BooleanField(default=False)
    cantidad_recibida = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Detalle de Orden'
        verbose_name_plural = 'Detalles de Orden'

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
        
        # Actualizar totales de la orden
        if self.orden:
            self.orden.calcular_totales()

    def clean(self):
        """Validación adicional para el detalle"""
        if self.cantidad <= 0:
            raise ValidationError("La cantidad debe ser mayor a cero")
        if self.precio_unitario <= 0:
            raise ValidationError("El precio unitario debe ser mayor a cero")

    def __str__(self):
        return f"{self.producto} x {self.cantidad}"

class RecepcionCompra(models.Model):
    TIPO_PAGO_CHOICES = [
        ('EFECTIVO', 'Efectivo'),
        ('TARJETA', 'Tarjeta'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('MIXTO', 'Mixto'),
    ]
    orden = models.ForeignKey(OrdenCompra, on_delete=models.PROTECT, related_name='recepciones')
    fecha = models.DateTimeField(auto_now_add=True)
    recibido_por = models.ForeignKey(PerfilUsuario, on_delete=models.PROTECT)
    almacen = models.ForeignKey(Almacen, on_delete=models.PROTECT)
    notas = models.TextField(blank=True)
    tipo_pago = models.CharField(max_length=20, choices=TIPO_PAGO_CHOICES, blank=True)

    class Meta:
        verbose_name = 'Recepción de Compra'
        verbose_name_plural = 'Recepciones de Compras'

    def __str__(self):
        return f"Recepción de {self.orden}"

@receiver(post_save, sender=DetalleOrdenCompra)
def actualizar_precio_producto(sender, instance, created, **kwargs):
    """
    Actualiza el precio de compra del producto cuando se recibe
    """
    if instance.recibido and instance.cantidad_recibida > 0:
        producto = instance.producto
        producto.precio_compra = instance.precio_unitario
        producto.save()





class CuentaPorPagar(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('PAGADA', 'Pagada'),
        ('VENCIDA', 'Vencida'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    orden_compra = models.OneToOneField(
        OrdenCompra,
        on_delete=models.CASCADE,
        related_name='cuenta_por_pagar'
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='PENDIENTE'
    )
    saldo_pendiente = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateField()
    fecha_pago = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Cuenta por Pagar'
        verbose_name_plural = 'Cuentas por Pagar'
        ordering = ['fecha_vencimiento']
    
    def __str__(self):
        return f"Cuenta por Pagar - OC-{self.orden_compra.numero}"
    
    def save(self, *args, **kwargs):
        # Actualizar estado según fechas
        hoy = timezone.now().date()
        if self.estado != 'PAGADA' and hoy > self.fecha_vencimiento:
            self.estado = 'VENCIDA'
        super().save(*args, **kwargs)
    
    @property
    def dias_vencimiento(self):
        """Devuelve días restantes o vencidos"""
        hoy = timezone.now().date()
        return (self.fecha_vencimiento - hoy).days
    
    @property
    def esta_vencida(self):
        return self.estado == 'VENCIDA'


# En compras/models.py

class PagoProveedor(models.Model):
    FORMA_PAGO_CHOICES = [
        ('EFECTIVO', 'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('CHEQUE', 'Cheque'),
        ('TARJETA', 'Tarjeta'),
    ]
    
    cuenta = models.ForeignKey(
        CuentaPorPagar,
        on_delete=models.CASCADE,
        related_name='pagos'
    )
    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    forma_pago = models.CharField(
        max_length=20,
        choices=FORMA_PAGO_CHOICES
    )
    fecha_pago = models.DateField(default=timezone.now)
    comprobante = models.CharField(
        max_length=50,
        blank=True
    )
    notas = models.TextField(blank=True)
    caja = models.ForeignKey(
        'caja.Caja',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    movimiento_caja = models.ForeignKey(
        'caja.MovimientoCaja',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = 'Pago a Proveedor'
        verbose_name_plural = 'Pagos a Proveedores'
        ordering = ['-fecha_pago']
    
    def __str__(self):
        return f"Pago de {self.monto} para OC-{self.cuenta.orden_compra.numero}"
    
    def clean(self):
        if self.monto <= 0:
            raise ValidationError("El monto debe ser mayor a cero")
    

    @transaction.atomic
    def revertir(self, usuario):
        """Revierte este pago y actualiza todos los estados"""
        # Revertir movimiento de caja si existe
        if self.movimiento_caja:
            movimiento_reversion = MovimientoCaja.objects.create(
                caja=self.movimiento_caja.caja,
                tipo='INGRESO',
                monto=self.monto,
                responsable=usuario,
                descripcion=f"Reversión de pago {self.comprobante}",
                comprobante=f"REV-{self.comprobante}"
            )
        
        # Actualizar cuenta por pagar
        cuenta = self.cuenta
        cuenta.saldo_pendiente += self.monto
        
        if cuenta.estado == 'PAGADA':
            cuenta.estado = 'VENCIDA' if cuenta.esta_vencida else 'PENDIENTE'
            cuenta.fecha_pago = None
        
        cuenta.save()
        
        # Eliminar este pago
        self.delete()
    
    @transaction.atomic
    def save(self, *args, **kwargs):
        # Validar antes de guardar
        self.full_clean()
        
        # Si es nuevo pago, actualizar saldos
        if not self.pk:
            # Registrar movimiento de caja si se especificó
            if self.caja and self.caja.estado == 'ABIERTA':
                movimiento = MovimientoCaja.objects.create(
                    caja=self.caja,
                    tipo='EGRESO',
                    monto=self.monto,
                    responsable=self.cuenta.orden_compra.creado_por,
                    descripcion=f"Pago OC-{self.cuenta.orden_compra.numero}",
                    comprobante=self.comprobante
                )
                self.movimiento_caja = movimiento
            
            # Validar que el monto no exceda el saldo pendiente
            if self.monto > self.cuenta.saldo_pendiente:
                raise ValidationError("El monto no puede ser mayor al saldo pendiente")
            
            # Actualizar saldos
            self.cuenta.saldo_pendiente -= self.monto
            if self.cuenta.saldo_pendiente <= 0:
                self.cuenta.estado = 'PAGADA'
                self.cuenta.orden_compra.estado = 'PAGADA'
                self.cuenta.fecha_pago = self.fecha_pago
            self.cuenta.save()
            self.cuenta.orden_compra.save()
        
        super().save(*args, **kwargs)



# En compras/models.py

@receiver(post_save, sender=OrdenCompra)
def crear_cuenta_por_pagar(sender, instance, created, **kwargs):
    """Crea automáticamente una cuenta por pagar cuando se recibe una orden a crédito"""
    if instance.estado == 'RECIBIDA' and instance.condicion == '2':  # Crédito
        CuentaPorPagar.objects.get_or_create(
            orden_compra=instance,
            defaults={
                'saldo_pendiente': instance.total,
                'fecha_vencimiento': instance.fecha_vencimiento or (timezone.now() + timezone.timedelta(days=30)).date()
            }
        )





