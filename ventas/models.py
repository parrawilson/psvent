from django.db import models
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from almacen.models import Producto, Servicio, Almacen, Stock, MovimientoInventario
from usuarios.models import PerfilUsuario
from caja.models import MovimientoCaja
from empresa.models import PuntoExpedicion, SecuenciaDocumento
from django.core.validators import RegexValidator
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date, timedelta
from decimal import Decimal

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



    # Agregar estos nuevos campos
    numero_cuotas = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(36)],
        verbose_name="Número de Cuotas"
    )
    monto_cuota = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Monto por Cuota"
    )
    entrega_inicial = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Entrega Inicial"
    )
    dia_vencimiento_cuotas = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(28)],
        verbose_name="Día de Vencimiento de Cuotas"
    )
    fecha_primer_vencimiento = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha Primer Vencimiento"
    )

    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-fecha']
    

    @property
    def comisiones(self):
        """Acceso directo a las comisiones asociadas"""
        return self.comisiones.all()

    def generar_comisiones(self):
        """Genera las comisiones para esta venta"""
        from .models import ComisionVenta  # Importación local para evitar circular
        
        # Eliminada la validación de estado para permitir generación antes de finalizar
        configuraciones = ConfiguracionComision.objects.filter(
            vendedor=self.vendedor,
            activo=True
        )
        
        comisiones = []
        for config in configuraciones:
            monto = config.calcular_comision(self)
            if monto > 0:
                comision = ComisionVenta.objects.create(
                    venta=self,
                    vendedor=self.vendedor,
                    configuracion=config,
                    tipo=config.tipo,
                    monto=monto
                )
                comisiones.append(comision)
        
        return comisiones

    @property
    def total_comisiones(self):
        """Total de comisiones generadas por esta venta"""
        return self.comisiones.aggregate(Sum('monto'))['monto__sum'] or Decimal('0.00')

    @property
    def comisiones_pendientes(self):
        """Comisiones pendientes de pago"""
        return self.comisiones.filter(estado='PENDIENTE')

    @property
    def comisiones_pagadas(self):
        """Comisiones ya pagadas"""
        return self.comisiones.filter(estado='PAGADA')

    def actualizar_estado_credito(self):
        """Actualiza el estado general del crédito basado en las cuotas"""
        if self.condicion != '2':  # Solo para ventas a crédito
            return
        
        # Verificar si todas las cuotas están pagadas
        cuotas_pendientes = self.cuentas_por_cobrar.exclude(estado='PAGADA')
        
        if not cuotas_pendientes.exists():
            # Todas las cuotas pagadas (no debería pasar si acabamos de revertir un pago)
            self.estado = 'FINALIZADA'
        else:
            # Hay cuotas pendientes
            self.estado = 'FINALIZADA'  # O mantener FINALIZADA si ese es tu flujo
        
        self.save()

    def tiene_servicios_con_inventario(self):
        """
        Verifica si la venta contiene servicios que consumen productos del inventario.
        Retorna True si hay al menos un servicio compuesto en los detalles de la venta.
        """
        return self.detalles.filter(
            tipo='SERVICIO',
            servicio__tipo='COMPUESTO'
        ).exists()


    def clean(self):
        # Validaciones existentes...
        
        # Validaciones para crédito
        if self.condicion == '2':
            if not self.dia_vencimiento_cuotas or self.dia_vencimiento_cuotas > 28:
                raise ValidationError("El día de vencimiento debe ser entre 1 y 28")
            
            if self.entrega_inicial and self.entrega_inicial >= self.total:
                raise ValidationError("La entrega inicial debe ser menor al total")
            
            if self.entrega_inicial < 0:
                raise ValidationError("La entrega inicial no puede ser negativa")
            
            if self.fecha_primer_vencimiento and self.fecha_primer_vencimiento < self.fecha.date():
                raise ValidationError("La fecha del primer vencimiento no puede ser anterior a la fecha de venta")


    def crear_cuotas(self):
        """
        Crea las cuotas para esta venta a crédito, considerando:
        - Entrega inicial (si existe)
        - Día fijo de vencimiento
        - Fecha primer vencimiento
        """
        if self.condicion != '2' or self.numero_cuotas <= 0:
            return []
            
        # Eliminar cuotas existentes si las hay
        self.cuentas_por_cobrar.all().delete()
        
        cuotas = []
        monto_total = self.total - self.entrega_inicial
        monto_cuota = monto_total / self.numero_cuotas
        
        # Si hay entrega inicial, crear registro especial
        if self.entrega_inicial > 0:
            cuota_inicial = CuentaPorCobrar.objects.create(
                venta=self,
                numero_cuota=0,
                monto=self.entrega_inicial,
                dia_vencimiento=self.dia_vencimiento_cuotas,
                fecha_vencimiento=self.fecha.date(),
                entrega_inicial=True,
                estado='PAGADA',  # Se asume que la entrega inicial se paga al momento
                saldo=0  # Asegurar saldo cero
            )
            cuotas.append(cuota_inicial)
        
        # Crear cuotas normales
        for i in range(1, self.numero_cuotas + 1):
            # Calcular fecha de vencimiento
            if i == 1 and self.fecha_primer_vencimiento:
                fecha_vencimiento = self.fecha_primer_vencimiento
            else:
                meses_a_sumar = i - (1 if self.fecha_primer_vencimiento else 0)
                fecha_vencimiento = self.calcular_fecha_vencimiento(meses_a_sumar)
            
            cuota = CuentaPorCobrar.objects.create(
                venta=self,
                numero_cuota=i,
                monto=monto_cuota,
                dia_vencimiento=self.dia_vencimiento_cuotas,
                fecha_vencimiento=fecha_vencimiento
            )
            cuotas.append(cuota)
        
        return cuotas
    
    def calcular_fecha_vencimiento(self, meses_a_sumar):
        """
        Calcula la fecha de vencimiento sumando meses pero manteniendo el día fijo
        Ej: Si día vencimiento es 5, siempre será día 5 de cada mes
        """
        fecha_base = self.fecha_primer_vencimiento if self.fecha_primer_vencimiento else self.fecha.date()
        
        # Sumar los meses
        year = fecha_base.year
        month = fecha_base.month + meses_a_sumar
        
        # Ajustar año si pasamos de diciembre
        while month > 12:
            month -= 12
            year += 1
        
        # Asegurarnos que el día no exceda los días del mes
        dia = min(self.dia_vencimiento_cuotas, 28)
        try:
            return date(year, month, dia)
        except ValueError:
            # Si el día no existe en ese mes (ej. 31 en abril), usar último día del mes
            ultimo_dia = (date(year, month + 1, 1) - timedelta(days=1)).day
            return date(year, month, min(dia, ultimo_dia))
    
    @property
    def total_pagado(self):
        """Total pagado en todas las cuotas (incluye entrega inicial)"""
        return sum(
        cuota.monto_pagado if not cuota.entrega_inicial else cuota.monto 
        for cuota in self.cuentas_por_cobrar.all()
    )
    
    @property
    def saldo_pendiente(self):
        """Saldo pendiente total"""
        total_cuotas_pendientes = sum(
            cuota.saldo 
            for cuota in self.cuentas_por_cobrar.exclude(entrega_inicial=True)
        )
        return max(total_cuotas_pendientes, Decimal('0.00'))
    
    @property
    def proxima_cuota(self):
        """Devuelve la próxima cuota pendiente"""
        return self.cuentas_por_cobrar.filter(
            estado__in=['PENDIENTE', 'VENCIDA', 'PARCIAL']
        ).order_by('numero_cuota').first()
    
    @property
    def cuotas_pagadas(self):
        return self.cuentas_por_cobrar.filter(estado='PAGADA').count()
    
    @property
    def cuotas_pendientes(self):
        return self.cuentas_por_cobrar.exclude(estado='PAGADA').count()

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
        
        # Actualizar datos de la venta (excepto estado)
        self.caja = caja
        self.tipo_pago = tipo_pago
        self.tipo_documento = tipo_documento
        self.condicion = condicion
        self.timbrado = timbrado if tipo_documento in ['F', 'BV'] else None
        self.generar_numero_documento()
        self.save()
        
        # Registrar movimiento de caja
        if condicion == '1' or (condicion == '2' and self.entrega_inicial > 0):
            MovimientoCaja.objects.create(
                caja=caja,
                tipo='INGRESO',
                monto=self.total if condicion == '1' else self.entrega_inicial,
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

        # Crear cuotas si es a crédito
        if condicion == '2':
            self.crear_cuotas()
        
        # Generar comisiones ANTES de marcar como FINALIZADA
        self.generar_comisiones()
        
        # Finalmente, actualizar el estado
        self.estado = 'FINALIZADA'
        self.save()
        


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






class CuentaPorCobrar(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('PAGADA', 'Pagada'),
        ('VENCIDA', 'Vencida'),
        ('CANCELADA', 'Cancelada'),
        ('PARCIAL', 'Pago Parcial'),
    ]
    
    TIPO_PAGO_CHOICES = [
        ('EFECTIVO', 'Efectivo'),
        ('TARJETA', 'Tarjeta'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('CHEQUE', 'Cheque'),
    ]
    
    venta = models.ForeignKey(
        'Venta', 
        on_delete=models.CASCADE, 
        related_name='cuentas_por_cobrar'
    )
    numero_cuota = models.PositiveIntegerField(
        verbose_name="Número de Cuota"
    )
    monto = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        verbose_name="Monto Total de la Cuota"
    )
    saldo = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        default=0,
        verbose_name="Saldo Pendiente"
    )
    dia_vencimiento = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(28)],
        verbose_name="Día de Vencimiento (mes)"
    )
    fecha_vencimiento = models.DateField(
        verbose_name="Fecha de Vencimiento"
    )
    fecha_pago = models.DateField(
        null=True, 
        blank=True,
        verbose_name="Fecha de Pago"
    )
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='PENDIENTE'
    )
    entrega_inicial = models.BooleanField(
        default=False,
        verbose_name="¿Es entrega inicial?"
    )
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cuenta por Cobrar'
        verbose_name_plural = 'Cuentas por Cobrar'
        ordering = ['venta', 'numero_cuota']
        unique_together = ['venta', 'numero_cuota']
    
    def __str__(self):
        return f"Cuota {self.numero_cuota} - Venta {self.venta.numero} - {self.get_estado_display()}"
    
    def clean(self):
        # Validar que el día de vencimiento sea válido
        if self.dia_vencimiento > 28:
            raise ValidationError("El día de vencimiento no puede ser mayor a 28")
        
        # Validar que la fecha de vencimiento coincida con el día establecido
        if self.fecha_vencimiento.day != self.dia_vencimiento:
            raise ValidationError(f"La fecha de vencimiento debe ser día {self.dia_vencimiento} del mes")
    
    def save(self, *args, **kwargs):
        # Calcular saldo pendiente si es nuevo
        if self._state.adding:
            self.saldo = self.monto
        
        # Si es entrega inicial y está pagada, saldo debe ser cero
        if self.entrega_inicial and self.estado == 'PAGADA':
            self.saldo = 0

        # Actualizar estado automáticamente
        self.actualizar_estado()
        
        super().save(*args, **kwargs)
    
    def actualizar_estado(self):
        """Actualiza el estado según fechas y pagos"""
        hoy = timezone.now().date()
        
        if self.estado == 'PAGADA':
            return
            
        if self.saldo <= 0:
            self.estado = 'PAGADA'
        elif hoy > self.fecha_vencimiento:
            self.estado = 'VENCIDA'
        elif self.saldo < self.monto:
            self.estado = 'PARCIAL'
        else:
            self.estado = 'PENDIENTE'
    
    def registrar_pago(self, monto, fecha_pago=None, tipo_pago='EFECTIVO', notas=''):
        """
        Registra un pago parcial o completo para esta cuota
        """
        if monto <= 0:
            raise ValidationError("El monto debe ser mayor a cero")
        
        if monto > self.saldo:
            raise ValidationError(f"Monto excede el saldo pendiente. Saldo: {self.saldo}")
        
        with transaction.atomic():
            # Registrar el pago
            PagoCuota.objects.create(
                cuenta=self,
                monto=monto,
                fecha_pago=fecha_pago or timezone.now().date(),
                tipo_pago=tipo_pago,
                notas=notas
            )
            
            # Actualizar saldo y estado
            self.saldo -= monto
            self.actualizar_estado()
            
            # Si se completó el pago, registrar fecha
            if self.estado == 'PAGADA' and not self.fecha_pago:
                self.fecha_pago = fecha_pago or timezone.now().date()
            
            self.save()
    
    @property
    def monto_pagado(self):
        """Devuelve el monto total pagado para esta cuota"""
        return self.monto - self.saldo
    
    @property
    def pagos(self):
        """Devuelve todos los pagos asociados a esta cuota"""
        return self.pagos.all().order_by('fecha_pago')
    
    @property
    def dias_vencido(self):
        """Devuelve los días de atraso si está vencida"""
        if self.estado != 'VENCIDA':
            return 0
        return (timezone.now().date() - self.fecha_vencimiento).days





class PagoCuota(models.Model):
    TIPO_PAGO_CHOICES = [
        ('EFECTIVO', 'Efectivo'),
        ('TARJETA', 'Tarjeta'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('CHEQUE', 'Cheque'),
    ]

    numero_recibo = models.CharField(max_length=20, blank=True, null=True)
    caja = models.ForeignKey(
        'caja.Caja', 
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    
    cuenta = models.ForeignKey(
        CuentaPorCobrar,
        on_delete=models.CASCADE,
        related_name='pagos'
    )
    monto = models.DecimalField(
        max_digits=12, 
        decimal_places=2
    )
    fecha_pago = models.DateField(
        default=timezone.now
    )
    tipo_pago = models.CharField(
        max_length=20,
        choices=TIPO_PAGO_CHOICES,
        default='EFECTIVO'
    )
    notas = models.TextField(
        blank=True,
        help_text="Observaciones sobre este pago"
    )

    cancelado = models.BooleanField(default=False)
    motivo_cancelacion = models.TextField(blank=True)
    cancelado_por = models.ForeignKey(
        'usuarios.PerfilUsuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pagos_cancelados'
    )
    fecha_cancelacion = models.DateTimeField(null=True, blank=True)

    registrado_por = models.ForeignKey(
        'usuarios.PerfilUsuario',
        on_delete=models.PROTECT,
        null=True
    )
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pago de Cuota'
        verbose_name_plural = 'Pagos de Cuotas'
        ordering = ['-fecha_pago']

    
    def generar_numero_recibo(self):
        """Genera el número de recibo usando la secuencia documental como en Ventas"""
        if not self.numero_recibo and self.caja:
            secuencia = SecuenciaDocumento.objects.filter(
                punto_expedicion=self.caja.punto_expedicion,
                tipo_documento='RECIBO_PAGO'
            ).first()
            
            if secuencia:
                self.numero_recibo = secuencia.generar_numero()
                self.save()
            else:
                # Si no existe secuencia, crear una automáticamente
                secuencia = SecuenciaDocumento.objects.create(
                    punto_expedicion=self.caja.punto_expedicion,
                    tipo_documento='RECIBO_PAGO',
                    siguiente_numero=1,
                    formato="{sucursal}-{punto}-{numero:07d}"
                )
                self.numero_recibo = secuencia.generar_numero()
                self.save()
        return self.numero_recibo
    
    @property
    def formato_numero_recibo(self):
        """Muestra el formato completo del recibo igual que en Ventas"""
        if self.numero_recibo and self.caja:
            return f"{self.caja.punto_expedicion.get_codigo_completo()}-{self.numero_recibo.split('-')[-1]}"
        return "Número no generado"
    
    def save(self, *args, **kwargs):
        # Asignar caja si no tiene (tomándola de la venta asociada)
        if not self.caja and hasattr(self, 'cuenta') and self.cuenta.venta.caja:
            self.caja = self.cuenta.venta.caja
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Pago de Gs. {self.monto} - {self.cuenta}"
    
    def save(self, *args, **kwargs):
        if not self.pk:  # Solo para creación
            self.registrado_por = self.registrado_por or getattr(self.cuenta.venta, 'vendedor', None)
        super().save(*args, **kwargs)
    
    @transaction.atomic
    def cancelar(self, usuario, motivo=""):
        """Cancela este pago y revierte sus efectos"""
        if self.cancelado:
            raise ValidationError("Este pago ya fue cancelado")
        
        cuenta = self.cuenta
        
        with transaction.atomic():
            # Revertir el movimiento de caja si existe
            if self.tipo_pago == 'EFECTIVO':
                movimiento = MovimientoCaja.objects.filter(
                    venta=cuenta.venta,
                    comprobante=f"P-{self.id}"
                ).first()
                
                if movimiento:
                    MovimientoCaja.objects.create(
                        caja=movimiento.caja,
                        tipo='EGRESO',
                        monto=movimiento.monto,
                        responsable=usuario,
                        descripcion=f"Cancelación de pago {self.id} - {movimiento.descripcion}",
                        venta=cuenta.venta,
                        comprobante=f"CP-{self.id}"
                    )
            
            # Actualizar la cuenta por cobrar
            cuenta.saldo += self.monto
            if cuenta.saldo > 0:
                if cuenta.saldo < cuenta.monto:
                    cuenta.estado = 'PARCIAL'
                else:
                    cuenta.estado = 'PENDIENTE'
                
                # Si estaba marcada como pagada, limpiar fecha de pago
                cuenta.fecha_pago = None
            cuenta.save()
            
            # Marcar el pago como cancelado
            self.cancelado = True
            self.motivo_cancelacion = motivo
            self.cancelado_por = usuario
            self.fecha_cancelacion = timezone.now()
            self.save()

            # Actualizar estado de la venta si es necesario
            cuenta.venta.actualizar_estado_credito()

from django.db.models import Q
# models.py (añadir al final)
class ConfiguracionComision(models.Model):
    TIPO_COMISION_CHOICES = [
        ('PORCENTAJE_VENTA', 'Porcentaje sobre venta total'),
        ('ENTREGA_INICIAL', 'Entrega inicial como comisión'),
    ]

    vendedor = models.ForeignKey(
        PerfilUsuario, 
        on_delete=models.CASCADE,
        related_name='configuraciones_comision',
        limit_choices_to=Q(es_vendedor=True) | Q(usuario__is_staff=True)
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_COMISION_CHOICES,
        default='PORCENTAJE_VENTA'
    )
    porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Porcentaje de comisión",
        null=True,
        blank=True
    )
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración de Comisión'
        verbose_name_plural = 'Configuraciones de Comisiones'
        unique_together = ['vendedor', 'tipo']

    def __str__(self):
        if self.tipo == 'PORCENTAJE_VENTA':
            return f"{self.vendedor} - {self.porcentaje}% sobre venta"
        return f"{self.vendedor} - Entrega inicial como comisión"

    def calcular_comision(self, venta):
        """
        Calcula el monto de comisión según el tipo de configuración
        """
        if self.tipo == 'PORCENTAJE_VENTA' and self.porcentaje:
            return (venta.total * self.porcentaje) / 100
        elif self.tipo == 'ENTREGA_INICIAL' and venta.condicion == '2':  # Solo para crédito
            return venta.entrega_inicial
        return Decimal('0.00')



class ComisionVenta(models.Model):
    """
    Registro de comisiones generadas por ventas
    """
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente de pago'),
        ('PARCIAL', 'Pago Parcial'),
        ('PAGADA', 'Pagada'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    venta = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        related_name='comisiones'
    )

    notas_credito = models.ManyToManyField(
        'NotaCredito',
        through='ComisionNotaCredito',
        related_name='comisiones_afectadas',
        blank=True
    )
    vendedor = models.ForeignKey(
        PerfilUsuario,
        on_delete=models.PROTECT,
        related_name='comisiones_ventas'
    )
    configuracion = models.ForeignKey(
        ConfiguracionComision,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    tipo = models.CharField(
        max_length=20,
        choices=ConfiguracionComision.TIPO_COMISION_CHOICES
    )
    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    monto_pagado = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0, 
        verbose_name="Monto Pagado"
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='PENDIENTE'
    )
    fecha_pago = models.DateField(
        null=True,
        blank=True
    )
    notas = models.TextField(
        blank=True,
        help_text="Observaciones sobre esta comisión"
    )
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Comisión por Venta'
        verbose_name_plural = 'Comisiones por Ventas'
        ordering = ['-creado']

    def __str__(self):
        return f"Comisión {self.get_tipo_display()} - Venta {self.venta.numero}"

    @classmethod
    def generar_comisiones(cls, venta):
        """
        Genera las comisiones para una venta según la configuración del vendedor
        """
        if venta.estado != 'FINALIZADA':
            return []
        
        configuraciones = ConfiguracionComision.objects.filter(
            vendedor=venta.vendedor,
            activo=True
        )
        
        comisiones = []
        for config in configuraciones:
            monto = config.calcular_comision(venta)
            if monto > 0:
                comision = cls.objects.create(
                    venta=venta,
                    vendedor=venta.vendedor,
                    configuracion=config,
                    tipo=config.tipo,
                    monto=monto
                )
                comisiones.append(comision)
        
        return comisiones
    

    def pagar(self, monto=None, fecha_pago=None):
        """Marca la comisión como pagada o parcialmente pagada"""
        if monto is None:
            monto = self.monto - self.monto_pagado
        
        self.monto_pagado += monto
        
        if self.monto_pagado >= self.monto:
            self.estado = 'PAGADA'
            self.monto_pagado = self.monto  # Asegurar que no exceda
        else:
            self.estado = 'PARCIAL'
            
        self.fecha_pago = fecha_pago or timezone.now().date()
        self.save()
    
    @property
    def saldo_pendiente(self):
        """Calcula el saldo pendiente de pago"""
        return self.monto - self.monto_pagado

    @transaction.atomic
    def revertir_pago(self, usuario, motivo=""):
        """Revierte un pago de comisión y registra el movimiento correspondiente en caja"""
        if self.estado != 'PAGADA':
            raise ValidationError("Solo se pueden revertir comisiones pagadas")
        
        # Buscar el movimiento de caja original
        movimiento = MovimientoCaja.objects.filter(
            comprobante__startswith=f"COM-{self.id}",
            tipo='EGRESO'
        ).order_by('-fecha').first()
        
        if not movimiento:
            raise ValidationError("No se encontró el movimiento de caja asociado")
        
        with transaction.atomic():
            # Generar timestamp único para el comprobante de reversión
            timestamp = int(timezone.now().timestamp())
            # Crear movimiento de entrada (reversión)
            MovimientoCaja.objects.create(
                caja=movimiento.caja,
                tipo='INGRESO',  # Entrada porque estamos recuperando el dinero
                monto=self.monto_pagado,
                responsable=usuario,
                descripcion=f"Reversión comisión venta {self.venta.numero}. Motivo: {motivo}",
                comprobante=f"COM-REV-{self.id}-{timestamp}",  # Incluir timestamp único
                
            )
            
            # Actualizar estado de la comisión
            self.estado = 'PENDIENTE'
            self.monto_pagado = Decimal('0.00')
            self.fecha_pago = None
            self.notas = f"\n--- REVERSIÓN ---\nMotivo: {motivo}\nUsuario: {usuario}\nFecha: {timezone.now().strftime('%Y-%m-%d %H:%M')}\n\n{self.notas or ''}"
            self.save()





class ConfiguracionComisionCobrador(models.Model):
    """Configuración de comisiones para cobradores"""
    cobrador = models.ForeignKey(
        PerfilUsuario, 
        on_delete=models.CASCADE,
        related_name='configuraciones_comision_cobrador',
        limit_choices_to=Q(es_cobrador=True) | Q(usuario__is_staff=True)
    )
    porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Porcentaje de comisión"
    )
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración de Comisión para Cobrador'
        verbose_name_plural = 'Configuraciones de Comisiones para Cobradores'
        unique_together = ['cobrador', 'activo']

    def __str__(self):
        return f"{self.cobrador} - {self.porcentaje}% sobre cobros"

    def calcular_comision(self, monto_cobrado):
        """Calcula el monto de comisión según el porcentaje configurado"""
        return (monto_cobrado * self.porcentaje) / 100


class ComisionCobrador(models.Model):
    """Registro de comisiones generadas por cobros realizados"""
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente de pago'),
        ('PARCIAL', 'Pago Parcial'),
        ('PAGADA', 'Pagada'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    pago = models.ForeignKey(
        PagoCuota,
        on_delete=models.CASCADE,
        related_name='comisiones_cobrador'
    )
    cobrador = models.ForeignKey(
        PerfilUsuario,
        on_delete=models.PROTECT,
        related_name='comisiones_cobros'
    )
    configuracion = models.ForeignKey(
        ConfiguracionComisionCobrador,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    monto_pagado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Monto Pagado"
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='PENDIENTE'
    )
    fecha_pago = models.DateField(
        null=True,
        blank=True
    )
    notas = models.TextField(
        blank=True,
        help_text="Observaciones sobre esta comisión"
    )
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Comisión por Cobro'
        verbose_name_plural = 'Comisiones por Cobros'
        ordering = ['-creado']

    def __str__(self):
        return f"Comisión Cobro #{self.pago.id} - {self.get_estado_display()}"

    # Modificar el método pagar para manejar pagos parciales
    def pagar(self, monto, fecha_pago=None):
        """Marca la comisión como pagada o parcialmente pagada"""
        self.monto_pagado += monto
        
        if self.monto_pagado >= self.monto:
            self.estado = 'PAGADA'
            self.monto_pagado = self.monto  # Asegurar que no exceda
        else:
            self.estado = 'PARCIAL'
            
        self.fecha_pago = fecha_pago or timezone.now().date()
        self.save()

    @transaction.atomic
    def revertir_pago(self, usuario, motivo=""):
        """Revierte un pago de comisión"""
        if self.estado != 'PAGADA':
            raise ValidationError("Solo se pueden revertir comisiones pagadas")
        
        # Buscar el movimiento de caja original (usando startswith)
        movimiento = MovimientoCaja.objects.filter(
            comprobante__startswith=f"COM-COB-{self.id}-",
            tipo='EGRESO'
        ).order_by('-fecha').first()  # Tomar el más reciente
        
        if not movimiento:
            raise ValidationError("No se encontró el movimiento de caja asociado")
        
        with transaction.atomic():
            # Generar timestamp único para el comprobante de reversión
            timestamp = int(timezone.now().timestamp())
            # Crear movimiento de entrada (reversión)
            MovimientoCaja.objects.create(
                caja=movimiento.caja,
                tipo='INGRESO',  # Entrada porque estamos recuperando el dinero
                monto=self.monto,
                responsable=usuario,
                descripcion=f"Reversión comisión cobro {self.pago.id}. Motivo: {motivo}",
                comprobante=f"COM-COB-REV-{self.id}-{timestamp}",  # Incluir timestamp único
                fecha=timezone.now().date()  # Asegurar fecha actual
            )
            
            # Actualizar estado de la comisión
            self.estado = 'PENDIENTE'
            self.fecha_pago = None
            self.notas = f"\n--- REVERSIÓN ---\nMotivo: {motivo}\nUsuario: {usuario}\nFecha: {timezone.now().strftime('%Y-%m-%d %H:%M')}\n\n{self.notas or ''}"
            self.save()


#Sección de Notas de Créditos
from decimal import Decimal, ROUND_HALF_UP

def redondear_dos_decimales(valor):
    """Redondea a 2 decimales, siempre devuelve un Decimal válido."""
    if valor is None:
        return Decimal('0.00')
    return Decimal(str(valor)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


class NotaCredito(models.Model):
    ESTADO_CHOICES = [
        ('BORRADOR', 'Borrador'),
        ('FINALIZADA', 'Finalizada'),
        ('CANCELADA', 'Cancelada'),
    ]

    TIPO_NOTA = [
        ('TOTAL', 'Cancelación total'),
        ('PARCIAL', 'Devolución parcial'),
    ]

    venta = models.ForeignKey(Venta, on_delete=models.PROTECT, related_name='notas_credito')
    numero = models.CharField(max_length=20, unique=True)
    numero_documento = models.CharField(max_length=15, blank=True)
    timbrado = models.ForeignKey(Timbrado, on_delete=models.PROTECT, null=True, blank=True)
    tipo = models.CharField(max_length=10, choices=TIPO_NOTA, default='TOTAL')
    fecha = models.DateTimeField(auto_now_add=True)
    motivo = models.TextField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='BORRADOR')
    caja = models.ForeignKey('caja.Caja', on_delete=models.PROTECT, null=True, blank=True)
    creado_por = models.ForeignKey(PerfilUsuario, on_delete=models.PROTECT)
    notas = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Nota de Crédito'
        verbose_name_plural = 'Notas de Crédito'
        ordering = ['-fecha']

    def __str__(self):
        return f"NC-{self.numero} (Venta: {self.venta.numero})"

    @property
    def punto_expedicion(self):
        return self.caja.punto_expedicion if self.caja else None

    @property
    def secuencia_documento(self):
        if not self.caja:
            return None
        return SecuenciaDocumento.objects.filter(
            punto_expedicion=self.caja.punto_expedicion,
            tipo_documento='NOTA_CREDITO'
        ).first()

    def generar_numero_documento(self):
        if not self.numero_documento and self.secuencia_documento:
            self.numero_documento = self.secuencia_documento.generar_numero()
            self.save()
        return self.numero_documento

    @property
    def formato_numero_documento(self):
        if self.numero_documento:
            return f"{self.punto_expedicion.get_codigo_completo()}-{self.numero_documento.split('-')[-1]}"
        return "Número no generado"

    @transaction.atomic
    def finalizar(self):
        if self.estado != 'BORRADOR':
            raise ValidationError('Solo se pueden finalizar notas de crédito en estado Borrador')

        if not self.caja or self.caja.estado != 'ABIERTA':
            raise ValidationError('La caja debe estar abierta para registrar notas de crédito')

        # Generar número de documento
        self.generar_numero_documento()

        # Registrar movimiento de caja (egreso por devolución)
        MovimientoCaja.objects.create(
            caja=self.caja,
            tipo='EGRESO',
            monto=redondear_dos_decimales(self.total),
            responsable=self.creado_por,
            descripcion=f"Nota de Crédito {self.numero} - Venta {self.venta.numero}",
            comprobante=f"NC-{self.numero}",
            nota_credito=self
        )

        # Revertir inventario
        for detalle in self.detalles.all():
            if detalle.detalle_venta.tipo == 'PRODUCTO':
                MovimientoInventario.objects.create(
                    producto=detalle.detalle_venta.producto,
                    almacen=detalle.detalle_venta.almacen,
                    cantidad=detalle.cantidad,
                    tipo='ENTRADA',
                    usuario=self.creado_por,
                    motivo=f"Nota de Crédito {self.numero}"
                )
            elif detalle.detalle_venta.tipo == 'SERVICIO' and detalle.detalle_venta.servicio.tipo == 'COMPUESTO':
                for componente in detalle.detalle_venta.servicio.componentes.all():
                    cantidad_necesaria = componente.cantidad * detalle.cantidad
                    MovimientoInventario.objects.create(
                        producto=componente.producto,
                        almacen=detalle.detalle_venta.almacen_servicio,
                        cantidad=cantidad_necesaria,
                        tipo='ENTRADA',
                        usuario=self.creado_por,
                        motivo=f"Nota de Crédito {self.numero} - Servicio {detalle.detalle_venta.servicio.nombre}"
                    )

        # Revertir comisiones
        self.revertir_comisiones()

        # Actualizar estado
        self.estado = 'FINALIZADA'
        self.save()

    @transaction.atomic
    def revertir_comisiones(self):
        porcentaje_devolucion = Decimal('1.00')
        if self.tipo == 'PARCIAL':
            porcentaje_devolucion = self.total / self.venta.total

        for comision in self.venta.comisiones.all():
            monto_a_revertir = redondear_dos_decimales(comision.monto * porcentaje_devolucion)

            if comision.estado == 'PAGADA':
                timestamp = int(timezone.now().timestamp())
                comprobante = f"COM-NC-REV-{comision.id}-{timestamp}"

                MovimientoCaja.objects.create(
                    caja=self.caja,
                    tipo='INGRESO',
                    monto=monto_a_revertir,
                    responsable=self.creado_por,
                    descripcion=f"Reversión comisión por NC {self.numero} - Venta {self.venta.numero}",
                    comprobante=comprobante
                )

                if self.tipo == 'TOTAL':
                    comision.estado = 'CANCELADA'
                    comision.monto_pagado = Decimal('0.00')
                else:
                    comision.monto_pagado = max(comision.monto_pagado - monto_a_revertir, Decimal('0.00'))
                    comision.estado = 'PARCIAL' if comision.monto_pagado > 0 else 'PENDIENTE'

                comision.notas = f"\n--- REVERSIÓN POR NC {self.numero} ---\nMonto revertido: Gs. {monto_a_revertir:,.2f}\n\n{comision.notas or ''}"
                comision.save()

            elif comision.estado in ['PENDIENTE', 'PARCIAL']:
                if self.tipo == 'TOTAL':
                    comision.estado = 'CANCELADA'
                    comision.monto = Decimal('0.00')
                else:
                    comision.monto = max(comision.monto - monto_a_revertir, Decimal('0.00'))
                    if comision.monto <= 0:
                        comision.estado = 'CANCELADA'

                comision.notas = f"\n--- AJUSTE POR NC {self.numero} ---\nMonto reducido: Gs. {monto_a_revertir:,.2f}\n\n{comision.notas or ''}"
                comision.save()

    @transaction.atomic
    def revertir_reversion_comisiones(self, usuario):
        for comision in self.venta.comisiones.all():
            movimientos_reversion = MovimientoCaja.objects.filter(
                comprobante__startswith=f"COM-NC-REV-{comision.id}-",
                tipo='INGRESO'
            )
            if movimientos_reversion.exists():
                total_revertido = redondear_dos_decimales(sum(m.monto for m in movimientos_reversion))
                timestamp = int(timezone.now().timestamp())
                comprobante = f"COM-NC-CANC-{comision.id}-{timestamp}"

                MovimientoCaja.objects.create(
                    caja=self.caja,
                    tipo='EGRESO',
                    monto=total_revertido,
                    responsable=usuario,
                    descripcion=f"Cancelación reversión comisión por NC {self.numero}",
                    comprobante=comprobante
                )

                if self.tipo == 'TOTAL':
                    comision.estado = 'PAGADA'
                    comision.monto_pagado = comision.monto
                else:
                    comision.monto_pagado += total_revertido
                    comision.estado = 'PAGADA' if comision.monto_pagado >= comision.monto else 'PARCIAL'

            comision.notas = f"\n--- CANCELACIÓN NC {self.numero} ---\nReversión de comisión revertida\n\n{comision.notas or ''}"
            comision.save()

    @transaction.atomic
    def cancelar(self, usuario):
        if self.estado != 'FINALIZADA':
            raise ValidationError('Solo se pueden cancelar notas de crédito finalizadas')

        movimiento_caja = MovimientoCaja.objects.filter(nota_credito=self).first()
        if movimiento_caja:
            MovimientoCaja.objects.create(
                caja=movimiento_caja.caja,
                tipo='INGRESO',
                monto=redondear_dos_decimales(movimiento_caja.monto),
                responsable=usuario,
                descripcion=f"Cancelación Nota de Crédito {self.numero}",
                comprobante=f"CNC-{self.numero}"
            )

        # Revertir inventario
        movimientos_inventario = MovimientoInventario.objects.filter(
            motivo=f"Nota de Crédito {self.numero}"
        )
        for movimiento in movimientos_inventario:
            MovimientoInventario.objects.create(
                producto=movimiento.producto,
                almacen=movimiento.almacen,
                cantidad=movimiento.cantidad,
                tipo='SALIDA',
                usuario=usuario,
                motivo=f"Cancelación Nota de Crédito {self.numero}"
            )

        self.revertir_reversion_comisiones(usuario)

        self.estado = 'CANCELADA'
        self.save()


class DetalleNotaCredito(models.Model):
    nota_credito = models.ForeignKey(NotaCredito, on_delete=models.CASCADE, related_name='detalles')
    detalle_venta = models.ForeignKey(DetalleVenta, on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Detalle de Nota de Crédito'
        verbose_name_plural = 'Detalles de Notas de Crédito'

    def clean(self):
        if self.cantidad <= 0:
            raise ValidationError("La cantidad debe ser mayor a cero")
        if self.cantidad > self.detalle_venta.cantidad:
            raise ValidationError("La cantidad no puede ser mayor a la originalmente vendida")
        # Redondeo seguro
        self.cantidad = Decimal(str(self.cantidad)).quantize(Decimal('0.001'))
        self.precio_unitario = redondear_dos_decimales(self.precio_unitario)

    def save(self, *args, **kwargs):
        if self.cantidad:
            self.cantidad = Decimal(str(self.cantidad)).quantize(Decimal('0.001'))
        if self.precio_unitario:
            self.precio_unitario = redondear_dos_decimales(self.precio_unitario)
        # calcular subtotal seguro
        self.subtotal = redondear_dos_decimales(self.cantidad * self.precio_unitario)
        super().save(*args, **kwargs)


class ComisionNotaCredito(models.Model):
    comision = models.ForeignKey(ComisionVenta, on_delete=models.CASCADE)
    nota_credito = models.ForeignKey(NotaCredito, on_delete=models.CASCADE)
    monto_revertido = models.DecimalField(max_digits=12, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['comision', 'nota_credito']