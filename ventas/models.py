from django.db import models
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from almacen.models import Producto, Servicio, Almacen, Stock, MovimientoInventario
from usuarios.models import PerfilUsuario
from caja.models import MovimientoCaja
from empresa.models import PuntoExpedicion, SecuenciaDocumento
from django.core.validators import RegexValidator


class Cliente(models.Model):
    TIPO_CONTRIBUYENTE = (
        ('1', 'Persona Física'),
        ('2', 'Persona Jurídica'),
    )
    TIPO_NATURALEZA = [
        ('1', 'Contribuyente'),
        ('2', 'No Contribuyente'),   
    ]
    TIPO_DOCUMENTO_CHOICES = [
        ('1', 'Cédula paraguaya'),
        ('2', 'Pasaporte'),
        ('3', 'Cédula extranjera'),
        ('4', 'Carnet de residencia'),
        ('5', 'Innominado'),
        ('6', 'Tarjeta Diplomática de exoneración fiscal'),
    ]

    TIPO_CLIENTE_CHOICES = [
        ('MINORISTA', 'Minorista'),
        ('MAYORISTA', 'Mayorista'),   
    ]

    pais_cod = models.CharField(max_length=5, default='PRY')
    pais = models.CharField(max_length=50, default='Paraguay')
    naturaleza = models.CharField(max_length=3, choices=TIPO_NATURALEZA, default='2')
    t_contribuyente = models.CharField(max_length=1, choices=TIPO_CONTRIBUYENTE, blank=True)
    tipo_documento = models.CharField(max_length=3, choices=TIPO_DOCUMENTO_CHOICES, default='1')
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



class Timbrado(models.Model):
    TIPO_EMISION_CHOICES = [
        ('FISICO', 'Comprobante Físico'),
        ('ELECTRONICO', 'Comprobante Electrónico'),
    ]
    
    ESTADO_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('VENCIDO', 'Vencido'),
    ]

    numero = models.CharField(
        max_length=8,
        unique=True,
        verbose_name='Número de Timbrado',
        validators=[RegexValidator(r'^\d{8}$', 'Debe ser un número de 8 dígitos')]
    )
    tipo_emision = models.CharField(
        max_length=20,
        choices=TIPO_EMISION_CHOICES,
        default='ELECTRONICO',
        verbose_name='Tipo de Emisión'
    )
    fecha_inicio = models.DateField(verbose_name='Fecha de Inicio Vigencia')
    fecha_fin = models.DateField(verbose_name='Fecha de Fin Vigencia')
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='ACTIVO',
        editable=False
    )
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Timbrado'
        verbose_name_plural = 'Timbrados'
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"Timbrado {self.numero}"

    def clean(self):
        # Validar fechas
        if self.fecha_inicio >= self.fecha_fin:
            raise ValidationError("La fecha de inicio debe ser anterior a la fecha de fin")

    def save(self, *args, **kwargs):
        # Actualizar estado según fechas
        hoy = timezone.now().date()
        if hoy > self.fecha_fin:
            self.estado = 'VENCIDO'
        else:
            self.estado = 'ACTIVO'
        
        super().save(*args, **kwargs)

    @property
    def vigente(self):
        """Indica si el timbrado está vigente"""
        hoy = timezone.now().date()
        return self.activo and self.fecha_inicio <= hoy <= self.fecha_fin


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
    ]

    TIPO_CONDICION =[
        ('1','CONTADO'),
        ('2','CREDITO'),
    ]

    numero = models.CharField(max_length=20, unique=True)
    tipo_documento = models.CharField(max_length=20,choices=TIPO_DOCUMENTO, default='T')
    numero_documento = models.CharField(max_length=15,blank=True)
    timbrado = models.ForeignKey(Timbrado, on_delete=models.PROTECT, null=True, blank=True)
    condicion = models.CharField(max_length=20,choices=TIPO_CONDICION, null=True, blank=True)
    num_doc_asociado = models.CharField(max_length=15,blank=True)
    timbrado_asociado = models.CharField(
        max_length=8,
        blank=True,
        null=True,
        verbose_name='Timbrado Documento Asociado',
        validators=[RegexValidator(r'^\d{8}$', 'Debe ser un número de 8 dígitos')]
    )
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

    @property
    def formato_numero_preview(self):
        """Devuelve el formato del número de documento para previsualización"""
        if not self.caja or not self.tipo_documento:
            return None
            
        # Obtener el prefijo del punto de expedición
        prefijo = self.caja.punto_expedicion.get_codigo_completo()
        
        # Si ya tenemos número, mostrarlo completo
        if self.numero_documento:
            return self.numero_documento
            
        # Si no, mostrar solo el prefijo
        return f"{prefijo}-[Número secuencial]"

    
    def calcular_totales(self):
        """Calcula los totales basados en los detalles"""
        detalles = self.detalles.all()
        self.total = sum(detalle.subtotal for detalle in detalles)
        self.save()
    

    @property
    def punto_expedicion(self):
        """Obtiene el punto de expedición a través de la caja"""
        return self.caja.punto_expedicion if self.caja else None
    
    @property
    def secuencia_documento(self):
        """Obtiene la secuencia documental según el tipo de documento"""
        if not self.caja or not self.tipo_documento:
            return None
            
        tipo_secuencia = {
            'F': 'FACTURA',
            'T': 'TICKET'
        }.get(self.tipo_documento)
        
        if tipo_secuencia:
            return SecuenciaDocumento.objects.filter(
                punto_expedicion=self.caja.punto_expedicion,
                tipo_documento=tipo_secuencia
            ).first()
        return None
    
    
    
    def generar_numero_documento(self):
        """Genera el número de documento usando la secuencia"""
        if not self.numero_documento and self.secuencia_documento:
            self.numero_documento = self.secuencia_documento.generar_numero()
            self.save()
        return self.numero_documento
    
    
    @property
    def formato_numero_documento(self):
        """Muestra el formato completo del documento"""
        if self.numero_documento:
            return f"{self.punto_expedicion.get_codigo_completo()}-{self.numero_documento.split('-')[-1]}"
        return "Número no generado"


    @transaction.atomic
    def finalizar(self, caja, tipo_pago, tipo_documento, condicion, timbrado=None):
        """Finaliza la venta y registra los movimientos"""
        if self.estado != 'BORRADOR':
            raise ValidationError('Solo se pueden finalizar ventas en estado Borrador')
        
        if caja.estado != 'ABIERTA':
            raise ValidationError('La caja debe estar abierta para registrar ventas')
        
        # Verificar stock para todos los productos y servicios
        for detalle in self.detalles.all():
            detalle.clean()  # Esto ejecutará las validaciones de stock
            
            if detalle.tipo == 'SERVICIO' and detalle.servicio.tipo == 'COMPUESTO':
                # Validar que tenga almacén asignado
                if not detalle.almacen_servicio:
                    almacen_servicio = Almacen.objects.filter(es_principal=True).first()
                    if not almacen_servicio:
                        raise ValidationError('No se encontró almacén principal para el servicio')
                    detalle.almacen_servicio = almacen_servicio
                    detalle.save()
        
        # Actualizar estado y datos de la venta
        self.caja = caja
        self.tipo_pago = tipo_pago
        self.tipo_documento = tipo_documento
        self.condicion = condicion
        self.timbrado = timbrado if tipo_documento in ['F', 'BV'] else None
        self.estado = 'FINALIZADA'
        self.generar_numero_documento()
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
        
        # Procesar cada detalle
        for detalle in self.detalles.all():
            if detalle.tipo == 'PRODUCTO':
                MovimientoInventario.objects.create(
                    producto=detalle.producto,
                    almacen=detalle.almacen,
                    cantidad=detalle.cantidad,
                    tipo='SALIDA',
                    usuario=self.vendedor,
                    motivo=f"Venta {self.numero}"
                )
            elif detalle.tipo == 'SERVICIO' and detalle.servicio.tipo == 'COMPUESTO':
                for componente in detalle.servicio.componentes.all():
                    cantidad_necesaria = componente.cantidad * detalle.cantidad
                    MovimientoInventario.objects.create(
                        producto=componente.producto,
                        almacen=detalle.almacen_servicio,
                        cantidad=cantidad_necesaria,
                        tipo='SALIDA',
                        usuario=self.vendedor,
                        motivo=f"Servicio {detalle.servicio.nombre} en Venta {self.numero}"
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
    TIPO_DETALLE_CHOICES = [
        ('PRODUCTO', 'Producto'),
        ('SERVICIO', 'Servicio'),
    ]
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    tipo = models.CharField(max_length=10, choices=TIPO_DETALLE_CHOICES, default='PRODUCTO')

    # Campos para productos
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, null=True, blank=True)
    almacen = models.ForeignKey(Almacen, on_delete=models.PROTECT, null=True, blank=True)
    
    # Campos para servicios
    servicio = models.ForeignKey(Servicio, on_delete=models.PROTECT, null=True, blank=True)
    almacen_servicio = models.ForeignKey(
        Almacen, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        related_name='detalles_servicio'
    )

    # Campos comunes
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    tasa_iva = models.PositiveIntegerField(default=10)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Detalle de Venta'
        verbose_name_plural = 'Detalles de Venta'
 
    def save(self, *args, **kwargs):
        # Validación de integridad
        if not (self.producto or self.servicio) or (self.producto and self.servicio):
            raise ValidationError("Debe especificar un producto O un servicio")
            
        if self.tipo == 'PRODUCTO' and not self.almacen:
            raise ValidationError("Debe especificar un almacén para productos")
            
        if self.tipo == 'SERVICIO' and self.servicio.tipo == 'COMPUESTO' and not self.almacen_servicio:
            raise ValidationError("Debe especificar un almacén para servicios que consumen productos")
            
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
        
        if self.venta:
            self.venta.calcular_totales()
    
    def clean(self):
        if self.cantidad <= 0:
            raise ValidationError("La cantidad debe ser mayor a cero")
        
        if self.precio_unitario <= 0:
            raise ValidationError("El precio unitario debe ser mayor a cero")
        
        # Validar stock para productos
        if self.tipo == 'PRODUCTO' and self.venta.estado == 'FINALIZADA':
            stock = Stock.objects.filter(
                producto=self.producto,
                almacen=self.almacen
            ).first()
            
            if stock and stock.cantidad < self.cantidad:
                raise ValidationError(f'Stock insuficiente. Disponible: {stock.cantidad}')
        
        # Validar stock para servicios que consumen productos
        if (self.tipo == 'SERVICIO' and self.servicio.tipo == 'COMPUESTO' and 
            self.venta.estado == 'FINALIZADA'):
            
            almacen = self.almacen_servicio or Almacen.objects.filter(es_principal=True).first()
            if not almacen:
                raise ValidationError('No se encontró almacén para el servicio')
            
            for componente in self.servicio.componentes.all():
                cantidad_necesaria = componente.cantidad * self.cantidad
                stock = Stock.objects.filter(
                    producto=componente.producto,
                    almacen=almacen
                ).first()
                
                if not stock or stock.cantidad < cantidad_necesaria:
                    raise ValidationError(
                        f'Stock insuficiente de {componente.producto.nombre} para el servicio {self.servicio.nombre}'
                    )

    def __str__(self):
        if self.tipo == 'PRODUCTO':
            return f"{self.producto} x {self.cantidad}"
        return f"{self.servicio} x {self.cantidad}"


