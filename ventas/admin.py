from django.contrib import admin
from .models import Venta, DetalleVenta, Cliente

class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0
    readonly_fields = ['subtotal']
    fields = ['producto', 'cantidad', 'precio_unitario', 'subtotal', 'almacen']
    can_delete = False

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'cliente', 'fecha', 'total', 'estado', 'vendedor')
    list_filter = ('estado', 'fecha')
    search_fields = ('numero', 'cliente__nombre_completo')
    inlines = [DetalleVentaInline]
    readonly_fields = ('subtotal', 'total', 'fecha')

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'tipo_documento', 'numero_documento', 'telefono')
    search_fields = ('nombre_completo', 'numero_documento')
    list_filter = ('tipo_documento',)
