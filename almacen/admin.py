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

from almacen.models import Servicio, ComponenteServicio
from django.core.exceptions import ValidationError

class ComponenteServicioInline(admin.TabularInline):
    model = ComponenteServicio
    extra = 1
    fields = ('producto', 'cantidad', 'observaciones')
    autocomplete_fields = ('producto',)
    verbose_name = 'Componente'
    verbose_name_plural = 'Componentes del Servicio'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "producto":
            kwargs["queryset"] = db_field.related_model.objects.filter(activo=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'tipo', 'precio', 'tasa_iva', 'activo', 'necesita_inventario', 'duracion_estimada_formatted')
    list_filter = ('tipo', 'activo', 'tasa_iva')
    search_fields = ('codigo', 'nombre', 'descripcion')
    list_editable = ('activo', 'precio', 'tasa_iva')
    readonly_fields = ('necesita_inventario', 'creado', 'actualizado')
    inlines = [ComponenteServicioInline]
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'descripcion', 'activo')
        }),
        ('Datos Comerciales', {
            'fields': ('tipo', 'precio', 'tasa_iva', 'duracion_estimada')
        }),
        ('Metadata', {
            'fields': ('necesita_inventario', 'creado', 'actualizado'),
            'classes': ('collapse',)
        }),
    )
    
    def duracion_estimada_formatted(self, obj):
        if obj.duracion_estimada:
            total_seconds = int(obj.duracion_estimada.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        return "-"
    duracion_estimada_formatted.short_description = 'Duración'
    
    def necesita_inventario(self, obj):
        return obj.necesita_inventario
    necesita_inventario.boolean = True
    necesita_inventario.short_description = 'Usa Inventario'
    
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            try:
                instance.clean()
                instance.save()
            except ValidationError as e:
                formset._non_form_errors = e.messages
                return
        formset.save_m2m()


@admin.register(ComponenteServicio)
class ComponenteServicioAdmin(admin.ModelAdmin):
    list_display = ('servicio', 'producto', 'cantidad', 'producto_unidad_medida')
    list_filter = ('servicio__tipo', 'servicio__activo')
    search_fields = ('servicio__nombre', 'producto__nombre')
    autocomplete_fields = ('servicio', 'producto')
    list_select_related = ('servicio', 'producto')
    
    def producto_unidad_medida(self, obj):
        return obj.producto.unidad_medida if obj.producto.unidad_medida else "-"
    producto_unidad_medida.short_description = 'Unidad'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'servicio', 'producto'
        ).filter(servicio__activo=True, producto__activo=True)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "servicio":
            kwargs["queryset"] = db_field.related_model.objects.filter(activo=True)
        elif db_field.name == "producto":
            kwargs["queryset"] = db_field.related_model.objects.filter(activo=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)