
from django.db import models
from django.db import transaction
from django.core.exceptions import ValidationError
from almacen.models import Producto, MovimientoInventario, Almacen
from usuarios.models import PerfilUsuario
from django.db.models.signals import post_save
from django.dispatch import receiver
from caja.models import MovimientoCaja

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
    ]

    numero = models.CharField(max_length=20, unique=True)
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
    def recibir(self, usuario, almacen, caja=None):
        """Marca la orden como recibida y actualiza inventario"""
        if self.estado != 'APROBADA':
            raise ValidationError('Solo se pueden recibir órdenes aprobadas')
        
        with transaction.atomic():
            # Registrar recepción
            recepcion = RecepcionCompra.objects.create(
                orden=self,
                recibido_por=usuario,
                almacen=almacen
            )
            
            # Registrar movimiento de caja si se especificó
            movimiento = None
            if caja and caja.estado == 'ABIERTA':
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
            self.caja = caja
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
    orden = models.ForeignKey(OrdenCompra, on_delete=models.PROTECT, related_name='recepciones')
    fecha = models.DateTimeField(auto_now_add=True)
    recibido_por = models.ForeignKey(PerfilUsuario, on_delete=models.PROTECT)
    almacen = models.ForeignKey(Almacen, on_delete=models.PROTECT)
    notas = models.TextField(blank=True)

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