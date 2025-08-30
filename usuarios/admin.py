from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from usuarios.models import PerfilUsuario

class PerfilInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Perfiles'
    filter_horizontal = ('sucursales',)
    fieldsets = (
        (None, {'fields': ('empresa', 'sucursales', 'tipo_usuario')}),
        ('Información personal', {
            'fields': ('cedula', 'telefono', 'direccion', 'tipo_doc', 'fecha_nacimiento', 'foto_perfil')
        }),
    )

class CustomUserAdmin(UserAdmin):
    inlines = (PerfilInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_tipo_usuario', 'is_staff')
    list_filter = ('perfil__tipo_usuario', 'is_staff', 'is_superuser', 'is_active')
    
    def get_tipo_usuario(self, obj):
        return obj.perfil.get_tipo_usuario_display()
    get_tipo_usuario.short_description = 'Tipo de Usuario'

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tipo_usuario', 'es_vendedor', 'es_cobrador', 'activo')
    list_filter = ('tipo_usuario', 'es_vendedor', 'es_cobrador', 'activo')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name', 'cedula')
    filter_horizontal = ('sucursales',)
