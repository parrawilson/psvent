from django.contrib import admin
from .models import Caja, MovimientoCaja

class MovimientoCajaInline(admin.TabularInline):
    model = MovimientoCaja
    extra = 0
    readonly_fields = ['fecha', 'responsable']
    fields = ['fecha', 'tipo', 'monto', 'descripcion', 'comprobante', 'responsable']
    can_delete = False

@admin.register(Caja)
class CajaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'responsable', 'estado', 'saldo_actual', 'fecha_apertura', 'fecha_cierre')
    list_filter = ('estado',)
    search_fields = ('nombre', 'responsable__usuario__username')
    inlines = [MovimientoCajaInline]
    readonly_fields = ('saldo_actual', 'fecha_apertura', 'fecha_cierre')

@admin.register(MovimientoCaja)
class MovimientoCajaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'caja', 'tipo', 'monto', 'descripcion', 'responsable')
    list_filter = ('tipo', 'caja')
    search_fields = ('descripcion', 'comprobante', 'caja__nombre')
    readonly_fields = ('fecha', 'responsable')
