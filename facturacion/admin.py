from django.contrib import admin
from .models import DocumentoElectronico

@admin.register(DocumentoElectronico)
class UnidadMedidaAdmin(admin.ModelAdmin):
    list_display = ('venta', 'estado')
    search_fields = ('venta', 'fecha_envio')
