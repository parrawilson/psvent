# usuarios/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Q
from empresa.models import Empresa, Sucursal

class PerfilUsuario(models.Model):
    TIPO_USUARIO_CHOICES = [
        ('ADMIN', 'Administrador'),
        ('ALMACEN', 'Personal de Almacén'),
        ('COMPRAS', 'Personal de Compras'),
        ('CAJA', 'Personal de Caja'),
        ('VENDEDOR', 'Vendedor'),
        ('COBRADOR', 'Cobrador'),
    ]

    TIPO_DOC = [
        ('1', 'Cédula paraguaya'),
        ('2', 'Pasaporte'),
        ('3', 'Cédula extranjera'),
        ('4', 'Carnet de residencia'),
        ('9', 'Otro'),
    ]

    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    empresa = models.ForeignKey(
        Empresa, 
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    sucursales = models.ManyToManyField(Sucursal, blank=True)
    cedula = models.CharField(max_length=20, unique=True, null=True, blank=True)
    telefono = models.CharField(max_length=20)
    direccion = models.TextField()
    tipo_usuario = models.CharField(max_length=10, choices=TIPO_USUARIO_CHOICES, default='ALMACEN')
    tipo_doc = models.CharField(max_length=10, choices=TIPO_DOC, default='1')
    fecha_nacimiento = models.DateField(null=True, blank=True)
    foto_perfil = models.ImageField(upload_to='perfiles/', null=True, blank=True)
    
    # Campos específicos para vendedores y cobradores
    es_vendedor = models.BooleanField(default=False, verbose_name="¿Es vendedor?")
    es_cobrador = models.BooleanField(default=False, verbose_name="¿Es cobrador?")
    activo = models.BooleanField(default=True, verbose_name="¿Activo?")
    
    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'
        ordering = ['usuario__username']
        permissions = [
            ("es_vendedor", "Puede realizar ventas y recibir comisiones"),
            ("es_cobrador", "Puede realizar cobros y recibir comisiones"),
        ]
    
    def __str__(self):
        return f"{self.usuario.get_full_name() or self.usuario.username} ({self.get_tipo_usuario_display()})"
    
    def save(self, *args, **kwargs):
        """Actualiza automáticamente los campos es_vendedor y es_cobrador según el tipo_usuario"""
        if self.tipo_usuario == 'VENDEDOR':
            self.es_vendedor = True
            self.es_cobrador = False
        elif self.tipo_usuario == 'COBRADOR':
            self.es_vendedor = False
            self.es_cobrador = True
        
        
        super().save(*args, **kwargs)
    
    @property
    def puede_recibir_comisiones(self):
        """Determina si este perfil puede recibir comisiones"""
        return self.es_vendedor or self.es_cobrador

# Señal para crear perfil automáticamente al crear usuario
@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.get_or_create(usuario=instance)