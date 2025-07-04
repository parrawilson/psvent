from django.db import models
from django.core.validators import MinValueValidator
from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver
from usuarios.models import PerfilUsuario

class UnidadMedida(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    abreviatura = models.CharField(max_length=10)
    descripcion = models.TextField(blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} ({self.abreviatura})"

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    TASA_CHOICES = [
        (10, 'Gravadas 10%'),
        (5, 'Gravadas 5%'),
        (0, 'Exentas'),
    ]
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='productos')
    unidad_medida = models.ForeignKey(UnidadMedida, on_delete=models.PROTECT)
    codigo = models.CharField(max_length=50, unique=True, blank=True, null=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    precio_compra = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    
    precio_venta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    tasa_iva = models.PositiveIntegerField(choices=TASA_CHOICES, default=10)
    stock_minimo = models.PositiveIntegerField(default=0)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)

    @property
    def margen_ganancia(self):
        """Calcula el margen de ganancia en porcentaje"""
        try:
            if self.precio_compra == 0:
                return 0
            return ((self.precio_venta - self.precio_compra) / self.precio_compra) * 100
        except (TypeError, AttributeError):
            return 0

    @property
    def ganancia_unitaria(self):
        """Calcula la ganancia por unidad con manejo de errores"""
        try:
            return float(self.precio_venta) - float(self.precio_compra)
        except (TypeError, AttributeError):
            return 0

    def __str__(self):
        return self.nombre

class Almacen(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    ubicacion = models.CharField(max_length=200)
    responsable = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nombre

class Stock(models.Model):
    producto = models.ForeignKey(
        Producto, 
        on_delete=models.CASCADE,
        related_name='inventarios'  # Solución al conflicto de nombres
    )
    almacen = models.ForeignKey(
        Almacen, 
        on_delete=models.CASCADE,
        related_name='inventarios'  # Relación inversa para almacén
    )
    cantidad = models.PositiveIntegerField(default=0)
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('producto', 'almacen')
        verbose_name_plural = "Stocks"
    
    def __str__(self):
        return f"{self.producto} en {self.almacen}: {self.cantidad}"


class MovimientoInventario(models.Model):
    TIPO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
        ('AJUSTE_FALTANTE', 'Ajuste por Faltante'),
        ('AJUSTE_SOBRANTE', 'Ajuste por Sobrante'),
    ]
    
    producto = models.ForeignKey('Producto', on_delete=models.PROTECT)
    almacen = models.ForeignKey('Almacen', on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    fecha = models.DateTimeField(auto_now_add=True)
    #usuario = models.ForeignKey('auth.User', on_delete=models.PROTECT)
    usuario = models.ForeignKey(PerfilUsuario, on_delete=models.PROTECT)

    motivo = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Movimiento de Inventario'
        verbose_name_plural = 'Movimientos de Inventario'
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.producto} ({self.cantidad})"

    def get_effect_on_stock(self):
        """Determina si el movimiento aumenta o disminuye el stock"""
        if self.tipo in ['ENTRADA', 'AJUSTE_SOBRANTE']:
            return 1  # Incremento
        return -1  # Decremento

    @transaction.atomic
    def save(self, *args, **kwargs):
        """
        Guarda el movimiento y actualiza el stock correspondiente.
        Maneja tanto creación como actualización.
        """
        # Obtener estado anterior si es una actualización
        if self.pk:
            old_mov = MovimientoInventario.objects.get(pk=self.pk)
            old_cantidad = old_mov.cantidad
            old_effect = old_mov.get_effect_on_stock()
            old_producto = old_mov.producto
            old_almacen = old_mov.almacen
        else:
            old_cantidad = 0
            old_effect = 0
            old_producto = None
            old_almacen = None

        # Guardar el movimiento primero
        super().save(*args, **kwargs)

        # Actualizar el stock
        current_effect = self.get_effect_on_stock()
        
        # Si es una actualización, revertir el efecto anterior
        if self.pk and (old_producto or old_almacen):
            self._update_stock(
                producto=old_producto,
                almacen=old_almacen,
                cantidad=old_cantidad,
                effect=-old_effect  # Revertir efecto anterior
            )
        
        # Aplicar el nuevo efecto
        self._update_stock(
            producto=self.producto,
            almacen=self.almacen,
            cantidad=self.cantidad,
            effect=current_effect
        )

    def _update_stock(self, producto, almacen, cantidad, effect):
        """Método helper para actualizar el stock"""
        stock, created = Stock.objects.get_or_create(
            producto=producto,
            almacen=almacen,
            defaults={'cantidad': 0}
        )
        
        stock.cantidad += (cantidad * effect)
        stock.save()

        # Actualizar última actualización del stock
        stock.ultima_actualizacion = self.fecha if hasattr(self, 'fecha') else timezone.now()
        stock.save()

    def clean(self):
        """Validación adicional para el movimiento"""
        super().clean()
        
        # Validar stock suficiente para salidas
        if self.tipo in ['SALIDA', 'AJUSTE_FALTANTE']:
            stock = Stock.objects.filter(
                producto=self.producto,
                almacen=self.almacen
            ).first()
            
            if stock and stock.cantidad < self.cantidad:
                raise ValidationError(
                    f'Stock insuficiente. Disponible: {stock.cantidad}'
                )

@receiver(post_delete, sender=MovimientoInventario)
def revert_stock_on_delete(sender, instance, **kwargs):
    """Señal para revertir el stock cuando se elimina un movimiento"""
    with transaction.atomic():
        stock = Stock.objects.filter(
            producto=instance.producto,
            almacen=instance.almacen
        ).first()
        
        if stock:
            effect = instance.get_effect_on_stock()
            stock.cantidad -= (instance.cantidad * effect)
            stock.save()