# usuarios/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from empresa.models import Empresa, Sucursal

class PerfilUsuario(models.Model):
    TIPO_USUARIO_CHOICES = [
        ('ADMIN', 'Administrador'),
        ('ALMACEN', 'Personal de Almacén'),
        ('COMPRAS', 'Personal de Compras'),
        ('CAJA', 'Personal de Caja'),
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
    cedula = models.CharField(max_length=20, unique=True, null=True, blank=True)  # Modificado
    telefono = models.CharField(max_length=20)
    direccion = models.TextField()
    tipo_usuario = models.CharField(max_length=10, choices=TIPO_USUARIO_CHOICES, default='ALMACEN')
    tipo_doc = models.CharField(max_length=10, choices=TIPO_DOC, default='1')
    fecha_nacimiento = models.DateField(null=True, blank=True)
    foto_perfil = models.ImageField(upload_to='perfiles/', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'
        ordering = ['usuario__username']
    
    def __str__(self):
        return f"Perfil de {self.usuario.username}"

# Señal para crear perfil automáticamente al crear usuario

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """Señal para crear perfil solo si no existe"""
    if created:
        PerfilUsuario.objects.get_or_create(usuario=instance)

# Elimina la segunda señal guardar_perfil_usuario ya que no es necesaria