
from django.db import models
from django.urls import reverse
from django.core.validators import RegexValidator
from django.utils import timezone





class Empresa(models.Model):
    # Información básica
    TIPO_REGIMEN = (
        ('1', 'Régimen de Turismo'),
        ('2', 'Importador'),
        ('3', 'Exportador'),
        ('4', 'Maquila'),
        ('5', 'Ley N° 60/90'),
        ('6', 'Régimen del Pequeño Productor'),
        ('7', 'Régimen del Mediano Productor'),
        ('8', 'Régimen Contable'),
    )
    TIPO_CONTRIBUYENTE = (
        ('1', 'Persona Física'),
        ('2', 'Persona Jurídica'),
    )
    nombre = models.CharField(max_length=300, verbose_name="Nombre Legal")
    nombre_comercial = models.CharField(
        max_length=300, 
        blank=True, 
        null=True,
        verbose_name="Nombre Comercial"
    )
    ruc = models.CharField(max_length=20, verbose_name="RUC", unique=True)
    dv = models.CharField(max_length=1, verbose_name="DV", blank=True)
    regimen = models.CharField(max_length=20, choices=TIPO_REGIMEN, default='6')
    t_contribuyente = models.CharField(max_length=1, choices=TIPO_CONTRIBUYENTE, default='1')
    
    # Ubicación
    direccion = models.CharField(verbose_name="Calle principal")
    calle_sec = models.CharField(verbose_name="Calle secundaria", blank= True)
    no_edificio = models.CharField(verbose_name="No edificio/piso/dto...",blank= True)
    departamento_codigo = models.CharField(max_length=3, blank=True, null=True)
    distrito_codigo = models.CharField(max_length=10, blank=True, null=True)
    ciudad_codigo = models.CharField(max_length=10, blank=True, null=True)
    barrio_codigo = models.CharField(max_length=10, blank=True, null=True)
    num_casa = models.CharField(max_length=5,verbose_name="No. de Casa",default= '0')
    # Contacto
    telefono = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    
    # Logotipo (para reportes)
    logo = models.ImageField(
        upload_to='empresas/logos/',
        blank=True,
        null=True,
        verbose_name="Logotipo"
    )
    
    # Metadata
    activa = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    @property
    def sucursal_principal(self):
        return self.sucursales.filter(es_principal=True).first()
    


    @property
    def departamento(self):
        from empresa.services.ubicaciones import UbicacionesService
        return UbicacionesService().get_nombre_departamento(self.departamento_codigo)
    
    @property
    def distrito(self):
        from empresa.services.ubicaciones import UbicacionesService
        return UbicacionesService().get_nombre_distrito(
            self.departamento_codigo, 
            self.distrito_codigo
        )
    
    @property
    def ciudad(self):
        from empresa.services.ubicaciones import UbicacionesService
        return UbicacionesService().get_nombre_ciudad(
            self.departamento_codigo,
            self.distrito_codigo,
            self.ciudad_codigo
        )
    
    @property
    def barrio(self):
        from empresa.services.ubicaciones import UbicacionesService
        return UbicacionesService().get_nombre_barrio(
            self.departamento_codigo,
            self.distrito_codigo,
            self.ciudad_codigo,
            self.barrio_codigo
        )

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.ruc})"

    def get_absolute_url(self):
        return reverse('empresa:editar_empresa', kwargs={'pk': self.pk})
    
    
    
class Sucursal(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='sucursales')
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=3, default='001')
    direccion = models.TextField()
    telefono = models.CharField(max_length=20)
    es_principal = models.BooleanField(default=False)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Sucursal"
        verbose_name_plural = "Sucursales"
        ordering = ["nombre"]
        unique_together = ('empresa', 'codigo')

    def __str__(self):
        return f"{self.nombre} ({self.empresa.nombre})"


class PuntoExpedicion(models.Model):
    TIPO_DOCUMENTO_CHOICES = [
        ('FACTURA', 'Factura'),
        ('TICKET', 'Ticket'),
        ('NOTA_CREDITO', 'Nota de Crédito'),
        ('NOTA_DEBITO', 'Nota de Débito'),
    ]
    
    sucursal = models.ForeignKey(
        Sucursal, 
        on_delete=models.PROTECT,
        related_name='puntos_expedicion',
        verbose_name='Sucursal'
    )
    codigo = models.CharField(
        max_length=3,
        verbose_name='Código',
        validators=[RegexValidator(r'^\d{3}$', 'Debe ser 3 dígitos')]
    )
    descripcion = models.CharField(
        max_length=100,
        verbose_name='Descripción'
    )
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Punto de Expedición'
        verbose_name_plural = 'Puntos de Expedición'
        unique_together = ('sucursal', 'codigo')
        ordering = ['sucursal', 'codigo']

    def __str__(self):
        return f"{self.sucursal.codigo}-{self.codigo} - {self.descripcion}"

    def get_codigo_completo(self):
        return f"{self.sucursal.codigo}-{self.codigo}"

    
    def crear_secuencias_iniciales(self):
        """Método explícito para crear secuencias con nuevo formato"""
        tipos = ['FACTURA', 'TICKET', 'NOTA_CREDITO', 'NOTA_DEBITO']
        for tipo in tipos:
            SecuenciaDocumento.objects.get_or_create(
                punto_expedicion=self,
                tipo_documento=tipo,
                defaults={
                    'formato': '{sucursal}-{punto}-{numero:07d}',
                    'siguiente_numero': 1
                }
                # El prefijo se autogenera en el save()
            )
        return self.secuencias.all()



class SecuenciaDocumento(models.Model):
    TIPO_DOCUMENTO_CHOICES = [
        ('FACTURA', 'Factura'),
        ('TICKET', 'Ticket'),
        ('NOTA_CREDITO', 'Nota de Crédito'),
        ('NOTA_DEBITO', 'Nota de Débito'),
    ]
    
    punto_expedicion = models.ForeignKey(
        PuntoExpedicion,
        on_delete=models.CASCADE,
        related_name='secuencias'
    )
    tipo_documento = models.CharField(
        max_length=20,
        choices=TIPO_DOCUMENTO_CHOICES
    )
    prefijo = models.CharField(
        max_length=7,  # 001-001 (3+1+3 caracteres)
        editable=False,  # Se autogenera
        default=''  # Se generará automáticamente
    )
    siguiente_numero = models.PositiveIntegerField(
        default=1
    )
    formato = models.CharField(
        max_length=50,
        default='{sucursal}-{punto}-{numero:07d}',
        editable=False,
        help_text="Formato fijo: CódigoSucursal-CódigoPunto-Número (001-001-0000001)"
    )
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('punto_expedicion', 'tipo_documento')
        verbose_name = 'Secuencia de Documento'
        verbose_name_plural = 'Secuencias de Documentos'

    def __str__(self):
        return f"{self.get_tipo_documento_display()} - {self.punto_expedicion} ({self.prefijo})"

    def save(self, *args, **kwargs):
        """Sobreescribir save para autogenerar prefijo y formato"""
        if not self.prefijo:
            self.prefijo = f"{self.punto_expedicion.sucursal.codigo}-{self.punto_expedicion.codigo}"
        
        if not self.formato:
            self.formato = '{sucursal}-{punto}-{numero:07d}'
        
        super().save(*args, **kwargs)

    def generar_numero(self):
        """Genera el siguiente número en la secuencia con formato 001-001-0000001"""
        numero = self.siguiente_numero
        self.siguiente_numero += 1
        self.save()
        
        return self.formato.format(
            sucursal=self.punto_expedicion.sucursal.codigo,
            punto=self.punto_expedicion.codigo,
            numero=numero
        )

    @property
    def codigo_sucursal(self):
        """Helper para obtener código de sucursal"""
        return self.punto_expedicion.sucursal.codigo

    @property
    def codigo_punto(self):
        """Helper para obtener código de punto"""
        return self.punto_expedicion.codigo




class ActividadesEconomicas(models.Model):
    """
    Modelo simple para almacenar códigos de actividades económicas y sus descripciones.
    """
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='actividades')
    codigo = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Código",
        help_text="Código de la actividad económica (ej: 62021)"
    )
    descripcion = models.CharField(
        max_length=255,
        verbose_name="Descripción",
        help_text="Descripción de la actividad económica"
    )
    es_principal = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Actividad Económica"
        verbose_name_plural = "Actividades Económicas"
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"