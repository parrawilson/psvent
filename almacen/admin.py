from django.contrib import admin
from .models import (
    UnidadMedida, Categoria, Producto, Almacen, MovimientoInventario,
    Stock, TipoConversion, ConversionProducto, ComponenteConversion,
    RegistroConversion, TrasladoProducto, DetalleTraslado
)

@admin.register(UnidadMedida)
class UnidadMedidaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'abreviatura_sifen')
    search_fields = ('nombre', 'abreviatura_sifen')

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'creado', 'activo')
    search_fields = ('nombre',)
    list_filter = ('activo',)
    readonly_fields = ('creado', 'actualizado')

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    def codigo_display(self, obj):
        return obj.codigo if obj.codigo else "N/A"
    codigo_display.short_description = "Código"

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj is None:
            form.base_fields['precio_minorista'].initial = 0
            form.base_fields['precio_mayorista'].initial = 0
        return form

    list_display = (
        'codigo_display', 'nombre', 'categoria',
        'unidad_medida', 'precio_minorista', 'precio_mayorista', 'activo'
    )
    list_filter = ('categoria', 'unidad_medida', 'activo')
    search_fields = ('nombre', 'codigo', 'descripcion')
    readonly_fields = ('creado', 'actualizado')

@admin.register(Almacen)
class AlmacenAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ubicacion', 'responsable', 'sucursal', 'creado')
    search_fields = ('nombre',)
    list_filter = ('activo',)
    readonly_fields = ('creado', 'actualizado')

@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ('producto', 'almacen', 'cantidad', 'tipo', 'usuario', 'fecha')
    search_fields = ('producto__nombre', 'motivo')
    list_filter = ('tipo', 'fecha')

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('producto', 'almacen', 'cantidad', 'ultima_actualizacion')
    search_fields = ('producto__nombre', 'almacen__nombre')
    list_filter = ('almacen',)

@admin.register(TipoConversion)
class TipoConversionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)

@admin.register(ConversionProducto)
class ConversionProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo_conversion', 'costo_adicional', 'activo')
    list_filter = ('activo', 'tipo_conversion')
    search_fields = ('nombre',)

@admin.register(ComponenteConversion)
class ComponenteConversionAdmin(admin.ModelAdmin):
    list_display = ('conversion', 'producto', 'tipo', 'cantidad')
    list_filter = ('tipo', 'conversion')
    search_fields = ('producto__nombre',)

@admin.register(RegistroConversion)
class RegistroConversionAdmin(admin.ModelAdmin):
    list_display = ('conversion', 'almacen', 'cantidad_ejecuciones', 'usuario', 'fecha', 'revertido')
    list_filter = ('revertido', 'almacen', 'conversion')
    search_fields = ('conversion__nombre', 'usuario__user__username')
    readonly_fields = ('fecha',)

@admin.register(TrasladoProducto)
class TrasladoProductoAdmin(admin.ModelAdmin):
    list_display = (
        'referencia', 'almacen_origen', 'almacen_destino',
        'estado', 'solicitante', 'responsable', 'fecha_solicitud', 'fecha_completado'
    )
    list_filter = ('estado', 'fecha_solicitud')
    search_fields = ('referencia', 'motivo')
    readonly_fields = ('fecha_solicitud', 'fecha_completado')

@admin.register(DetalleTraslado)
class DetalleTrasladoAdmin(admin.ModelAdmin):
    list_display = (
        'traslado', 'producto', 'cantidad_solicitada',
        'cantidad_enviada', 'cantidad_recibida'
    )
    search_fields = ('producto__nombre', 'traslado__referencia')
    list_filter = ('traslado__estado',)

