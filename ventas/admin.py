from django.contrib import admin
from .models import Venta, DetalleVenta, Cliente, Timbrado, CuentaPorCobrar, PagoCuota

class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0
    fields = ('tipo', 'producto', 'servicio', 'cantidad', 'precio_unitario', 'subtotal', 'almacen', 'almacen_servicio')
    readonly_fields = ('subtotal',)
    autocomplete_fields = ('producto', 'servicio', 'almacen', 'almacen_servicio')

class CuentaPorCobrarInline(admin.TabularInline):
    model = CuentaPorCobrar
    extra = 0
    readonly_fields = ('saldo', 'estado', 'dias_vencido')
    fields = ('numero_cuota', 'monto', 'saldo', 'fecha_vencimiento', 'estado', 'dias_vencido')
    can_delete = False
    
    def dias_vencido(self, obj):
        return obj.dias_vencido
    dias_vencido.short_description = 'Días vencido'

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'cliente', 'fecha', 'total', 'estado', 'vendedor', 'condicion', 'tipo_documento')
    list_filter = ('estado', 'fecha', 'condicion', 'tipo_documento', 'vendedor')
    search_fields = ('numero', 'cliente__nombre_completo', 'numero_documento')
    inlines = [DetalleVentaInline, CuentaPorCobrarInline]
    readonly_fields = ('subtotal', 'total', 'fecha', 'numero', 'vendedor')
    autocomplete_fields = ('cliente', 'timbrado', 'caja')
    list_select_related = ('cliente', 'vendedor')
    fieldsets = (
        (None, {
            'fields': ('numero', 'fecha', 'cliente', 'vendedor', 'estado', 'notas')
        }),
        ('Documentación', {
            'fields': ('tipo_documento', 'timbrado', 'numero_documento')
        }),
        ('Condiciones', {
            'fields': ('condicion', 'tipo_pago', 'caja',
                      ('entrega_inicial', 'numero_cuotas', 'monto_cuota'),
                      ('dia_vencimiento_cuotas', 'fecha_primer_vencimiento'))
        }),
        ('Totales', {
            'fields': ('subtotal', 'total')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'cliente', 'vendedor', 'timbrado', 'caja'
        )

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'tipo_documento', 'numero_documento', 'telefono', 'email', 'activo')
    search_fields = ('nombre_completo', 'numero_documento', 'telefono', 'email')
    list_filter = ('tipo_documento', 'tipo_cliente', 'activo', 'naturaleza')
    list_editable = ('activo',)
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombre_completo', 'tipo_cliente', 'activo')
        }),
        ('Documentación', {
            'fields': ('tipo_documento', 'numero_documento', 'dv')
        }),
        ('Contacto', {
            'fields': ('telefono', 'email', 'direccion')
        }),
        ('Datos Tributarios', {
            'fields': ('naturaleza', 't_contribuyente', 'pais', 'pais_cod')
        }),
    )

@admin.register(Timbrado)
class TimbradoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'tipo_emision', 'fecha_inicio', 'fecha_fin', 'estado', 'activo', 'vigente')
    list_filter = ('estado', 'tipo_emision', 'activo')
    search_fields = ('numero',)
    readonly_fields = ('estado', 'vigente')
    date_hierarchy = 'fecha_inicio'
    
    def vigente(self, obj):
        return obj.vigente
    vigente.boolean = True
    vigente.short_description = 'Vigente'

@admin.register(CuentaPorCobrar)
class CuentaPorCobrarAdmin(admin.ModelAdmin):
    list_display = ('venta', 'cliente', 'numero_cuota', 'monto', 'saldo', 'fecha_vencimiento', 'estado', 'dias_vencido')
    list_filter = ('estado', 'entrega_inicial', 'fecha_vencimiento')
    search_fields = ('venta__numero', 'venta__cliente__nombre_completo')
    readonly_fields = ('saldo', 'estado', 'dias_vencido', 'monto_pagado')
    date_hierarchy = 'fecha_vencimiento'
    fields = ('venta', 'numero_cuota', 'monto', 'saldo', 
              ('dia_vencimiento', 'fecha_vencimiento', 'fecha_pago'),
              'estado', 'entrega_inicial', 'dias_vencido', 'monto_pagado')
    
    def cliente(self, obj):
        return obj.venta.cliente
    cliente.short_description = 'Cliente'
    cliente.admin_order_field = 'venta__cliente'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'venta', 'venta__cliente'
        )

@admin.register(PagoCuota)
class PagoCuotaAdmin(admin.ModelAdmin):
    list_display = ('cuenta', 'monto', 'fecha_pago', 'tipo_pago', 'registrado_por')
    list_filter = ('tipo_pago', 'fecha_pago')
    search_fields = ('cuenta__venta__numero', 'cuenta__venta__cliente__nombre_completo', 'notas')
    date_hierarchy = 'fecha_pago'
    raw_id_fields = ('cuenta',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'cuenta', 'cuenta__venta', 'cuenta__venta__cliente', 'registrado_por'
        )
