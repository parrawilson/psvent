from django.db import models
from django.core.validators import MinValueValidator
from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.forms import ValidationError
from usuarios.models import PerfilUsuario
from empresa.models import Sucursal

class UnidadMedida(models.Model):
    ABREVIATURA_SIFEN_CHOICES = [
    ('77', 'Unidad - UNI'),
    ('87', 'Metros - m'),
    ('2366', 'Costo Por Mil - CPM'),
    ('2329', 'Unidad Internacional - UI'),
    ('110', 'Metros cúbicos - M3'),
    ('86', 'Gramos - g'),
    ('89', 'Litros - LT'),
    ('90', 'Miligramos - MG'),
    ('91', 'Centimetros - CM'),
    ('92', 'Centimetros cuadrados - CM2'),
    ('93', 'Centimetros cubicos - CM3'),
    ('94', 'Pulgadas - PUL'),
    ('96', 'Milímetros cuadrados - MM2'),
    ('79', 'Kilogramos s/ metro cuadrado - kg/m2'),
    ('97', 'Año - AA'),
    ('98', 'Mes - ME'),
    ('99', 'Tonelada - TN'),
    ('100', 'Hora - Hs'),
    ('101', 'Minuto - Mi'),
    ('104', 'Determinación - DET'),
    ('103', 'Yardas - Ya'),
    ('108', 'Metros - MT'),
    ('109', 'Metros cuadrados - M2'),
    ('95', 'Milímetros - MM'),
    ('666', 'Segundo - Se'),
    ('102', 'Día - Di'),
    ('83', 'Kilogramos - kg'),
    ('88', 'Mililitros - ML'),
    ('625', 'Kilómetros - Km'),
    ('660', 'Metro lineal - ml'),
    ('885', 'Unidad Medida Global - GL'),
    ('891', 'Por Milaje - pm'),
    ('869', 'Hectáreas - ha'),
    ('569', 'Ración - ración'),
    ]
    nombre = models.CharField(max_length=50, unique=True)
    abreviatura_sifen = models.CharField(choices=ABREVIATURA_SIFEN_CHOICES, default='77')
    descripcion = models.TextField(blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} ({self.abreviatura_sifen})"

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
    precio_minorista = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    
    precio_mayorista = models.DecimalField(
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


    def __str__(self):
        return self.nombre

class Almacen(models.Model):
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE, related_name='almacenes')
    nombre = models.CharField(max_length=100, unique=True)
    ubicacion = models.CharField(max_length=200)
    responsable = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)
    es_principal = models.BooleanField(
        default=False,
        verbose_name='Almacén Principal',
        help_text='Indica si este es el almacén principal de la sucursal'
    )
    
    class Meta:
        verbose_name = 'Almacén'
        verbose_name_plural = 'Almacenes'
        constraints = [
            models.UniqueConstraint(
                fields=['sucursal', 'es_principal'],
                condition=models.Q(es_principal=True),
                name='unico_almacen_principal_por_sucursal'
            )
        ]
    
    def __str__(self):
        return f"{self.nombre} ({self.sucursal})"

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


class TipoConversion(models.Model):
    """Define las formas en que un producto puede convertirse"""
    nombre = models.CharField(max_length=100)  # Ej: "Descomposición en paquetes pequeños"
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return f"{self.nombre} ({self.descripcion})"


class ConversionProducto(models.Model):
    """Relación flexible de conversiones posibles"""
    nombre = models.CharField(max_length=100, help_text="Nombre descriptivo de la conversión")
    tipo_conversion = models.ForeignKey(TipoConversion, on_delete=models.PROTECT)
    activo = models.BooleanField(default=True)
    costo_adicional = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Costo adicional total por conversión"
    )

    def __str__(self):
        return self.nombre

class ComponenteConversion(models.Model):
    """Componentes de una conversión"""
    TIPO_COMPONENTE = [
        ('ORIGEN', 'Producto Origen'),
        ('DESTINO', 'Producto Destino'),
    ]
    
    conversion = models.ForeignKey(ConversionProducto, on_delete=models.CASCADE, related_name='componentes')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=10, choices=TIPO_COMPONENTE)
    cantidad = models.PositiveIntegerField(
        help_text="Cantidad de este producto en la conversión"
    )

    class Meta:
        unique_together = ('conversion', 'producto', 'tipo')

class RegistroConversion(models.Model):
    """Auditoría de todas las conversiones realizadas"""
    conversion = models.ForeignKey(ConversionProducto, on_delete=models.PROTECT)
    almacen = models.ForeignKey(Almacen, on_delete=models.PROTECT)
    cantidad_ejecuciones = models.PositiveIntegerField(
        help_text="Cantidad de veces que se ejecutó esta conversión"
    )
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(PerfilUsuario, on_delete=models.PROTECT)
    motivo = models.TextField(blank=True)
    revertido = models.BooleanField(default=False)
    relacion_reversion = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.conversion.nombre} (x{self.cantidad_ejecuciones})"





class TrasladoProducto(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROCESO', 'En proceso'),
        ('COMPLETADO', 'Completado'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    referencia = models.CharField(max_length=50, unique=True)
    almacen_origen = models.ForeignKey(
        Almacen, 
        on_delete=models.PROTECT,
        related_name='traslados_salida'
    )
    almacen_destino = models.ForeignKey(
        Almacen, 
        on_delete=models.PROTECT,
        related_name='traslados_entrada'
    )
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_completado = models.DateTimeField(null=True, blank=True)
    solicitante = models.ForeignKey(
        PerfilUsuario,
        on_delete=models.PROTECT,
        related_name='traslados_solicitados'
    )
    responsable = models.ForeignKey(
        PerfilUsuario,
        on_delete=models.PROTECT,
        related_name='traslados_responsable',
        null=True,
        blank=True
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='PENDIENTE'
    )
    motivo = models.TextField()
    observaciones = models.TextField(blank=True)

    class Meta:
        ordering = ['-fecha_solicitud']
        verbose_name = 'Traslado de Productos'
        verbose_name_plural = 'Traslados de Productos'

    def __str__(self):
        return f"Traslado {self.referencia} - {self.almacen_origen} → {self.almacen_destino}"

    def save(self, *args, **kwargs):
        if not self.referencia:
            # Generar referencia automática (ejemplo: TR-20230615-001)
            from django.utils import timezone
            date_str = timezone.now().strftime('%Y%m%d')
            last_num = TrasladoProducto.objects.filter(
                referencia__startswith=f'TR-{date_str}'
            ).count()
            self.referencia = f'TR-{date_str}-{last_num + 1:03d}'
        super().save(*args, **kwargs)

class DetalleTraslado(models.Model):
    traslado = models.ForeignKey(
        TrasladoProducto,
        on_delete=models.CASCADE,
        related_name='detalles'
    )
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad_solicitada = models.PositiveIntegerField()
    cantidad_enviada = models.PositiveIntegerField(default=0)
    cantidad_recibida = models.PositiveIntegerField(default=0)
    observaciones = models.TextField(blank=True)

    class Meta:
        unique_together = ('traslado', 'producto')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_cantidad_enviada = self.cantidad_enviada
        self._original_cantidad_recibida = self.cantidad_recibida
    
    def has_changed(self, field=None):
        if field == 'cantidad_enviada':
            return self._original_cantidad_enviada != self.cantidad_enviada
        elif field == 'cantidad_recibida':
            return self._original_cantidad_recibida != self.cantidad_recibida
        else:
            return (self._original_cantidad_enviada != self.cantidad_enviada or 
                    self._original_cantidad_recibida != self.cantidad_recibida)
    
    def save(self, *args, **kwargs):
        # Guardar el detalle primero
        super().save(*args, **kwargs)
        
        # Verificar si todos los detalles tienen cantidad enviada igual a solicitada
        traslado = self.traslado
        detalles_completos = all(
            d.cantidad_enviada == d.cantidad_solicitada 
            for d in traslado.detalles.all()
        )
        
        # Actualizar estado del traslado si es necesario
        if detalles_completos and traslado.estado == 'PENDIENTE':
            traslado.estado = 'EN_PROCESO'
            traslado.save()
    def clean(self):
        super().clean()
        if self.cantidad_enviada > self.cantidad_solicitada:
            raise ValidationError('La cantidad enviada no puede ser mayor que la cantidad solicitada')
        
        if self.cantidad_recibida > self.cantidad_enviada:
            raise ValidationError('La cantidad recibida no puede ser mayor que la cantidad enviada')

    def __str__(self):
        return f"{self.producto} - {self.cantidad_solicitada} unidades"
    



from django.db import models
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from usuarios.models import PerfilUsuario
from empresa.models import Sucursal

# ... (otros modelos existentes)

class Servicio(models.Model):
    TIPO_SERVICIO_CHOICES = [
        ('SIMPLE', 'Servicio Simple'),
        ('COMPUESTO', 'Servicio Compuesto (usa productos)'),
    ]
    
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_SERVICIO_CHOICES, default='SIMPLE')
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tasa_iva = models.PositiveIntegerField(default=10)
    activo = models.BooleanField(default=True)
    duracion_estimada = models.DurationField(null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.nombre
    
    def clean(self):
        if self.precio < 0:
            raise ValidationError("El precio no puede ser negativo")
    
    @property
    def necesita_inventario(self):
        return self.tipo == 'COMPUESTO' and self.componentes.exists()

class ComponenteServicio(models.Model):
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name='componentes')
    producto = models.ForeignKey('Producto', on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=10, decimal_places=3)
    observaciones = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('servicio', 'producto')
        verbose_name = 'Componente de Servicio'
        verbose_name_plural = 'Componentes de Servicio'
    
    def __str__(self):
        return f"{self.servicio} - {self.producto} x {self.cantidad}"
    
    def clean(self):
        if self.cantidad <= 0:
            raise ValidationError("La cantidad debe ser mayor a cero")

# ... (resto de tus modelos existentes)
