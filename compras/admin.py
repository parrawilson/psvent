from django.contrib import admin
from .models import Proveedor, OrdenCompra, DetalleOrdenCompra, RecepcionCompra

class DetalleOrdenInline(admin.TabularInline):
    model = DetalleOrdenCompra
    extra = 1

@admin.register(OrdenCompra)
class OrdenCompraAdmin(admin.ModelAdmin):
    list_display = ('numero', 'proveedor', 'fecha', 'total', 'estado')
    list_filter = ('estado', 'proveedor')
    search_fields = ('numero', 'proveedor__razon_social')
    inlines = [DetalleOrdenInline]

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('razon_social', 'ruc', 'telefono', 'activo')
    search_fields = ('razon_social', 'ruc')

@admin.register(RecepcionCompra)
class RecepcionCompraAdmin(admin.ModelAdmin):
    list_display = ('orden', 'fecha', 'almacen', 'recibido_por')
    list_filter = ('almacen',)