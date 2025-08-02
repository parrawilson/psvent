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



from django.contrib import admin
from django.utils import timezone
from django.db.models import Sum, Q
from .models import CuentaPorPagar, PagoProveedor

@admin.register(CuentaPorPagar)
class CuentaPorPagarAdmin(admin.ModelAdmin):
    list_display = (
        'orden_compra_link',
        'proveedor',
        'saldo_pendiente',
        'fecha_vencimiento',
        'dias_restantes',
        'estado_colorizado',
        'acciones_pendientes'
    )
    list_filter = (
        'estado',
        ('fecha_vencimiento', admin.DateFieldListFilter),
        'orden_compra__proveedor',
    )
    search_fields = (
        'orden_compra__numero',
        'orden_compra__proveedor__razon_social',
        'orden_compra__proveedor__ruc'
    )
    readonly_fields = ('fecha_creacion', 'saldo_pendiente', 'dias_vencimiento')
    actions = ['marcar_como_pagadas', 'generar_recordatorios']
    date_hierarchy = 'fecha_vencimiento'
    
    fieldsets = (
        ('Información Principal', {
            'fields': (
                'orden_compra',
                'estado',
                'saldo_pendiente',
                'fecha_vencimiento',
                'fecha_pago'
            )
        }),
        ('Detalles Adicionales', {
            'fields': (
                'fecha_creacion',
                'dias_vencimiento'
            ),
            'classes': ('collapse',)
        }),
    )

    def orden_compra_link(self, obj):
        return f'<a href="/admin/compras/ordencompra/{obj.orden_compra.id}/change/">{obj.orden_compra.numero}</a>'
    orden_compra_link.short_description = 'Orden de Compra'
    orden_compra_link.allow_tags = True

    def proveedor(self, obj):
        return obj.orden_compra.proveedor.razon_social
    proveedor.short_description = 'Proveedor'
    proveedor.admin_order_field = 'orden_compra__proveedor__razon_social'

    def dias_restantes(self, obj):
        dias = obj.dias_vencimiento
        if dias > 0:
            return f'{dias} días'
        elif dias == 0:
            return 'Hoy'
        else:
            return f'Vencido ({abs(dias)} días)'
    dias_restantes.short_description = 'Días Restantes'

    def estado_colorizado(self, obj):
        colors = {
            'PENDIENTE': 'orange',
            'PAGADA': 'green',
            'VENCIDA': 'red',
            'CANCELADA': 'gray'
        }
        return f'<span style="color: {colors[obj.estado]}">{obj.get_estado_display()}</span>'
    estado_colorizado.short_description = 'Estado'
    estado_colorizado.allow_tags = True

    def acciones_pendientes(self, obj):
        if obj.estado == 'PENDIENTE':
            return f'<a href="/admin/compras/pagoproveedor/add/?cuenta={obj.id}">Registrar Pago</a>'
        return '-'
    acciones_pendientes.short_description = 'Acciones'
    acciones_pendientes.allow_tags = True

    def marcar_como_pagadas(self, request, queryset):
        updated = queryset.filter(estado='PENDIENTE').update(
            estado='PAGADA',
            fecha_pago=timezone.now().date()
        )
        self.message_user(request, f'{updated} cuentas marcadas como pagadas')
    marcar_como_pagadas.short_description = 'Marcar como pagadas (hoy)'

    def generar_recordatorios(self, request, queryset):
        # Lógica para enviar recordatorios (implementar según necesidades)
        self.message_user(request, 'Recordatorios programados para enviar')
    generar_recordatorios.short_description = 'Generar recordatorios'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related('orden_compra', 'orden_compra__proveedor')
        return qs

@admin.register(PagoProveedor)
class PagoProveedorAdmin(admin.ModelAdmin):
    list_display = (
        'fecha_pago',
        'cuenta_link',
        'proveedor',
        'monto_formateado',
        'forma_pago',
        'comprobante',
        'caja_link'
    )
    list_filter = (
        'forma_pago',
        ('fecha_pago', admin.DateFieldListFilter),
        'cuenta__orden_compra__proveedor',
    )
    search_fields = (
        'cuenta__orden_compra__numero',
        'comprobante',
        'cuenta__orden_compra__proveedor__razon_social'
    )
    raw_id_fields = ('cuenta', 'caja')
    date_hierarchy = 'fecha_pago'
    readonly_fields = ('saldo_restante',)
    
    fieldsets = (
        ('Información del Pago', {
            'fields': (
                'cuenta',
                'monto',
                'forma_pago',
                'fecha_pago',
                'comprobante'
            )
        }),
        ('Relación con Caja', {
            'fields': (
                'caja',
                'movimiento_caja'
            ),
            'classes': ('collapse',)
        }),
        ('Información Adicional', {
            'fields': (
                'notas',
                'saldo_restante'
            )
        }),
    )

    def cuenta_link(self, obj):
        return f'<a href="/admin/compras/cuentaporpagar/{obj.cuenta.id}/change/">{obj.cuenta.orden_compra.numero}</a>'
    cuenta_link.short_description = 'Orden de Compra'
    cuenta_link.allow_tags = True

    def proveedor(self, obj):
        return obj.cuenta.orden_compra.proveedor.razon_social
    proveedor.short_description = 'Proveedor'
    proveedor.admin_order_field = 'cuenta__orden_compra__proveedor__razon_social'

    def monto_formateado(self, obj):
        return f"Gs. {obj.monto:,.0f}"
    monto_formateado.short_description = 'Monto'
    monto_formateado.admin_order_field = 'monto'

    def caja_link(self, obj):
        if obj.caja:
            return f'<a href="/admin/caja/caja/{obj.caja.id}/change/">{obj.caja.nombre}</a>'
        return '-'
    caja_link.short_description = 'Caja'
    caja_link.allow_tags = True

    def saldo_restante(self, obj):
        return obj.cuenta.saldo_pendiente
    saldo_restante.short_description = 'Saldo Restante'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related('cuenta', 'cuenta__orden_compra', 'cuenta__orden_compra__proveedor', 'caja')
        return qs

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        cuenta_id = request.GET.get('cuenta')
        if cuenta_id:
            try:
                cuenta = CuentaPorPagar.objects.get(id=cuenta_id)
                initial.update({
                    'cuenta': cuenta,
                    'monto': cuenta.saldo_pendiente,
                    'fecha_pago': timezone.now().date()
                })
            except CuentaPorPagar.DoesNotExist:
                pass
        return initial