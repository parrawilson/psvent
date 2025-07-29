from django.contrib import admin

# Register your models here.

from .models import PerfilUsuario

class PerfilUsuario(admin.TabularInline):
    model = PerfilUsuario
    extra = 0
    readonly_fields = ['usuario', 'empresa']
    fields = ['usuario', 'empresa', 'telefono', 'tipo_usuario']
    can_delete = False
