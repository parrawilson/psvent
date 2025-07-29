from django.contrib import admin
from .models import Empresa,Sucursal, PuntoExpedicion

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ruc', 'telefono', 'activa')
    search_fields = ('nombre', 'ruc')

@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'direccion', 'activa')
    search_fields = ('nombre', 'codigo')

@admin.register(PuntoExpedicion)
class PuntoExpedicionlAdmin(admin.ModelAdmin):
    list_display = ('sucursal', 'codigo', 'descripcion')
    search_fields = ('sucursal', 'codigo')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:  # Solo para creación
            obj.crear_secuencias_iniciales()