from django.db import models
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from almacen.models import Producto, Almacen, Stock, MovimientoInventario
from usuarios.models import PerfilUsuario
from caja.models import MovimientoCaja


class Cliente(models.Model):
    TIPO_DOCUMENTO_CHOICES = [
        ('DNI', 'DNI'),
        ('RUC', 'RUC'),
        ('CE', 'Carnet de Extranjería'),
    ]

    TIPO_CLIENTE_CHOICES = [
        ('MINORISTA', 'Minorista'),
        ('MAYORISTA', 'Mayorista'),   
    ]

    tipo_documento = models.CharField(max_length=3, choices=TIPO_DOCUMENTO_CHOICES, default='DNI')
    numero_documento = models.CharField(max_length=20, unique=True)
    dv = models.CharField(max_length=2,blank=True)
    nombre_completo = models.CharField(max_length=200)
    direccion = models.TextField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    tipo_cliente= models.CharField(choices=TIPO_CLIENTE_CHOICES, default='MINORISTA')
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nombre_completo']

    def __str__(self):
        return f"{self.nombre_completo} ({self.tipo_documento}:{self.numero_documento})"

class Venta(models.Model):
    ESTADO_CHOICES = [
        ('BORRADOR', 'Borrador'),
        ('FINALIZADA', 'Finalizada'),
        ('CANCELADA', 'Cancelada'),
    ]

    TIPO_PAGO_CHOICES = [
        ('EFECTIVO', 'Efectivo'),
        ('TARJETA', 'Tarjeta'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('MIXTO', 'Mixto'),
    ]

    TIPO_DOCUMENTO = [
        ('F','FACTURA'),
        ('T','TICKET'),
        ('BV','BOLETA DE VENTA'),
    ]

    TIPO_CONDICION =[
        ('1','CONTADO'),
        ('2','CREDITO'),
    ]

    numero = models.CharField(max_length=20, unique=True)
    tipo_documento = models.CharField(max_length=20,choices=TIPO_DOCUMENTO, default='T')
    numero_documento = models.CharField(max_length=15,blank=True)
    timbrado = models.CharField(max_length=8, blank=True)
    condicion = models.CharField(max_length=20,choices=TIPO_CONDICION, null=True, blank=True)
    num_doc_asociado = models.CharField(max_length=15,blank=True)
    timbrado_asociado = models.CharField(max_length=8, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='BORRADOR')
    tipo_pago = models.CharField(max_length=20, choices=TIPO_PAGO_CHOICES, blank=True)
    caja = models.ForeignKey('caja.Caja', on_delete=models.PROTECT, null=True, blank=True)  # Usa string
    vendedor = models.ForeignKey(PerfilUsuario, on_delete=models.PROTECT)
    notas = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-fecha']

    def __str__(self):
        return f"Venta-{self.numero}"

    def calcular_totales(self):
        """Calcula los totales basados en los detalles"""
        detalles = self.detalles.all()
        self.total = sum(detalle.subtotal for detalle in detalles)
        self.save()


    @transaction.atomic
    def finalizar(self, caja, tipo_pago):
        """Finaliza la venta y registra los movimientos"""
        if self.estado != 'BORRADOR':
            raise ValidationError('Solo se pueden finalizar ventas en estado Borrador')
        
        if caja.estado != 'ABIERTA':
            raise ValidationError('La caja debe estar abierta para registrar ventas')
        
        # Verificar stock para todos los productos
        for detalle in self.detalles.all():
            stock = Stock.objects.filter(
                producto=detalle.producto,
                almacen=detalle.almacen
            ).first()
            
            if not stock or stock.cantidad < detalle.cantidad:
                raise ValidationError(f'Stock insuficiente para {detalle.producto.nombre}')
        
        # Actualizar estado y datos de la venta
        self.estado = 'FINALIZADA'
        self.tipo_pago = tipo_pago
        self.caja = caja
        self.save()
        
        # Registrar movimiento de caja
        MovimientoCaja.objects.create(
            caja=caja,
            tipo='INGRESO',
            monto=self.total,
            responsable=self.vendedor,
            descripcion=f"Venta {self.numero}",
            venta=self,
            comprobante=f"V-{self.numero}"
        )
        
        # Solo crear movimientos de inventario (ellos actualizarán el stock automáticamente)
        for detalle in self.detalles.all():
            MovimientoInventario.objects.create(
                producto=detalle.producto,
                almacen=detalle.almacen,
                cantidad=detalle.cantidad,
                tipo='SALIDA',
                usuario=self.vendedor,
                motivo=f"Venta {self.numero}"
            )



    @transaction.atomic
    def cancelar(self, usuario):
        """Cancela una venta y revierte los movimientos asociados"""
        if self.estado != 'FINALIZADA':
            raise ValidationError('Solo se pueden cancelar ventas finalizadas')
        
        # Revertir movimiento de caja si existe
        movimiento_caja = MovimientoCaja.objects.filter(venta=self).first()
        if movimiento_caja:
            MovimientoCaja.objects.create(
                caja=movimiento_caja.caja,
                tipo='EGRESO',
                monto=movimiento_caja.monto,
                responsable=usuario,
                descripcion=f"Cancelación Venta {self.numero}",
                venta=self,
                comprobante=f"NC-{self.numero}"
            )
        
        # Revertir movimientos de inventario (creando entradas por cada salida)
        movimientos_inventario = MovimientoInventario.objects.filter(
            motivo=f"Venta {self.numero}"
        )
        
        for movimiento in movimientos_inventario:
            MovimientoInventario.objects.create(
                producto=movimiento.producto,
                almacen=movimiento.almacen,
                cantidad=movimiento.cantidad,
                tipo='ENTRADA',
                usuario=usuario,
                motivo=f"Cancelación Venta {self.numero}"
            )
        
        # Actualizar estado de la venta
        self.estado = 'CANCELADA'
        self.save()


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    tasa_iva = models.PositiveIntegerField(default=10)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    almacen = models.ForeignKey(Almacen, on_delete=models.PROTECT)

    class Meta:
        verbose_name = 'Detalle de Venta'
        verbose_name_plural = 'Detalles de Venta'

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
        
        # Actualizar totales de la venta
        if self.venta:
            self.venta.calcular_totales()

    def clean(self):
        """Validación adicional para el detalle"""
        if self.cantidad <= 0:
            raise ValidationError("La cantidad debe ser mayor a cero")
        if self.precio_unitario <= 0:
            raise ValidationError("El precio unitario debe ser mayor a cero")
        
        # Verificar stock si la venta está finalizada
        if self.venta.estado == 'FINALIZADA':
            stock = Stock.objects.filter(
                producto=self.producto,
                almacen=self.almacen
            ).first()
            
            if stock and stock.cantidad < self.cantidad:
                raise ValidationError(f'Stock insuficiente. Disponible: {stock.cantidad}')

    def __str__(self):
        return f"{self.producto} x {self.cantidad}"
