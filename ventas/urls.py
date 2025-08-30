from django.urls import path
from . import views

app_name = 'ventas'

urlpatterns = [
    # Ventas
    path('', views.lista_ventas, name='lista_ventas'),
    path('nueva/', views.crear_venta, name='crear_venta'),
    path('<int:venta_id>/', views.detalle_venta, name='detalle_venta'),
    path('<int:venta_id>/editar/', views.editar_venta, name='editar_venta'),
    path('<int:venta_id>/finalizar/', views.finalizar_venta, name='finalizar_venta'),
    path('<int:venta_id>/cancelar/', views.cancelar_venta, name='cancelar_venta'),
    path('api/ventas/<int:venta_id>/detalles/', views.api_detalles_venta, name='api_detalles_venta'),
    
    # Clientes
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/nuevo/', views.crear_cliente, name='crear_cliente'),
    path('clientes/<int:cliente_id>/editar/', views.editar_cliente, name='editar_cliente'),
    path('clientes/<int:cliente_id>/eliminar/', views.eliminar_cliente, name='eliminar_cliente'),


    path('timbrados/', views.lista_timbrados, name='lista_timbrados'),
    path('timbrados/nuevo/', views.crear_timbrado, name='crear_timbrado'),
    path('timbrados/editar/<int:timbrado_id>/', views.editar_timbrado, name='editar_timbrado'),
    path('timbrados/eliminar/<int:timbrado_id>/', views.eliminar_timbrado, name='eliminar_timbrado'),


    # Cuentas por cobrar
    path('cuentas-por-cobrar/menu/', views.menu_ctas_cobrar, name='menu_ctas_cobrar'),
    path('cuentas-por-cobrar/', views.lista_cuentas_por_cobrar, name='lista_cuentas_por_cobrar'),
    path('cuentas-por-cobrar/cuenta/<int:cuenta_id>/', views.detalle_cuenta, name='detalle_cuenta'),
    path('cuentas-por-cobrar/cuenta/<int:cuenta_id>/pagar/', views.registrar_pago, name='registrar_pago'),
    path('cuentas-por-cobrar/pagos/', views.lista_pagos, name='lista_pagos'),
    path('cuentas-por-cobrar/pagos/<int:pago_id>/cancelar/', views.cancelar_pago, name='cancelar_pago'),
    path('cuentas-por-cobrar/pagos/<int:pago_id>/imprimir/<str:tipo>/', views.imprimir_recibo, name='imprimir_recibo_tipo'),
    path('cuentas-por-cobrar/pagos/<int:pago_id>/imprimir/', views.imprimir_recibo, name='imprimir_recibo'),
    path('cuentas-por-cobrar/cobros-rapidos/', views.cobros_rapidos, name='cobros_rapidos'),


    path('comisiones/menu/', views.menu_comsiones, name='menu_comisiones'),
    path('comisiones/lista/', views.lista_comisiones, name='lista_comisiones'),
    path('comisiones/pagar/<int:comision_id>/', views.pagar_comision, name='pagar_comision'),
    path('comisiones/configurar/', views.configurar_comisiones, name='configurar_comisiones'),
    path('comisiones/<int:comision_id>/revertir/', views.revertir_pago_comision, name='revertir_pago_comision'),
    path('comisiones/<int:comision_id>/', views.detalle_comision_vendedor, name='detalle_comision_vendedor'),

    path('configuraciones-comision/', views.lista_configuraciones_comision, name='lista_configuraciones_comision'),
    path('comisiones/pagos-rapidos/', views.pagos_rapidos_comisiones_vendedores, name='pagos_rapidos_comisiones_vendedores'),



    # Comisiones para cobradores
    path('comisiones-cobradores/', views.menu_comisiones_cobradores, name='menu_comisiones_cobradores'),
    path('comisiones-cobradores/configurar/lista/', views.lista_configuraciones_comision_cobradores, name='lista_configurar_comisiones_cobradores'),
    path('comisiones-cobradores/configurar/', views.configurar_comisiones_cobradores, name='configurar_comisiones_cobradores'),
    path('comisiones-cobradores/configurar/editar/<int:config_id>/', views.editar_configuracion_comision_cobrador, name='editar_configuracion_comision_cobrador'),
    path('comisiones-cobradores/configurar/desactivar/<int:config_id>/', views.desactivar_configuracion_comision_cobrador, name='desactivar_configuracion_comision_cobrador'),
    path('comisiones-cobradores/lista/', views.lista_comisiones_cobradores, name='lista_comisiones_cobradores'),
    path('comisiones-cobradores/pagar/<int:comision_id>/', views.pagar_comision_cobrador, name='pagar_comision_cobrador'),
    path('comisiones-cobradores/<int:comision_id>/revertir/', views.revertir_pago_comision_cobrador, name='revertir_pago_comision_cobrador'),
    path('comisiones-cobradores/<int:comision_id>/', views.detalle_comision_cobrador, name='detalle_comision_cobrador'),
    path('comisiones-cobradores/pagos-rapidos/', views.pagos_rapidos_comisiones_cobradores, name='pagos_rapidos_comisiones_cobradores'),
  
    # Notas de Crédito
    path('notas-credito/', views.lista_notas_credito, name='lista_notas_credito'),
    path('notas-credito/nueva/', views.crear_nota_credito, name='crear_nota_credito'),
    path('notas-credito/nueva/<int:venta_id>/', views.crear_nota_credito, name='crear_nota_credito_venta'),
    path('notas-credito/<int:nota_credito_id>/', views.detalle_nota_credito, name='detalle_nota_credito'),
    path('notas-credito/<int:nota_credito_id>/finalizar/', views.finalizar_nota_credito, name='finalizar_nota_credito'),
    path('notas-credito/<int:nota_credito_id>/cancelar/', views.cancelar_nota_credito, name='cancelar_nota_credito'),
    path('notas-credito/<int:nota_credito_id>/imprimir/', views.imprimir_nota_credito, name='imprimir_nota_credito'),
]