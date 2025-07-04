from django.contrib import admin
from .models import UnidadMedida, Categoria, Producto,Almacen,MovimientoInventario,Stock

@admin.register(MovimientoInventario)
class UnidadMedidaAdmin(admin.ModelAdmin):
    list_display = ('producto', 'almacen', 'cantidad', 'motivo')
    search_fields = ('producto', 'motivo')
    
@admin.register(Stock)
class UnidadMedidaAdmin(admin.ModelAdmin):
    list_display = ('producto', 'almacen', 'cantidad')
    search_fields = ('producto', 'almacen')


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'creado')
    search_fields = ('nombre',)
    list_filter = ('activo',)
    readonly_fields = ('creado', 'actualizado')


@admin.register(Almacen)
class AlmacenAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ubicacion', 'responsable', 'creado')
    search_fields = ('nombre',)
    list_filter = ('activo',)
    readonly_fields = ('creado', 'actualizado')

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    def codigo_display(self, obj):
        return obj.codigo if obj.codigo else "N/A"
    codigo_display.short_description = "Código"
    
    def margen_display(self, obj):
        return f"{obj.margen_ganancia:.2f}%" if obj.precio_compra else "N/A"
    margen_display.short_description = "Margen %"
    
    def ganancia_display(self, obj):
        return f"${obj.ganancia_unitaria:.2f}"
    ganancia_display.short_description = "Ganancia"

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Establecer valores por defecto para nuevos productos
        if obj is None:
            form.base_fields['precio_compra'].initial = 0
            form.base_fields['precio_venta'].initial = 0
        return form

    list_display = (
        'codigo_display',
        'nombre',
        'categoria',
        'unidad_medida',
        'precio_compra',
        'precio_venta',
        'ganancia_display',
        'margen_display',
        'activo'
    )
    
    list_filter = ('categoria', 'unidad_medida', 'activo')
    search_fields = ('nombre', 'codigo', 'descripcion')
    readonly_fields = ('ganancia_display', 'margen_display', 'creado', 'actualizado')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'descripcion', 'categoria', 'unidad_medida', 'imagen')
        }),
        ('Precios y Stock', {
            'fields': (
                'precio_compra',
                'precio_venta',
                ('ganancia_display', 'margen_display'),
                ('stock', 'stock_minimo')
            )
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
        ('Metadata', {
            'fields': ('creado', 'actualizado'),
            'classes': ('collapse',)
        }),
    )
