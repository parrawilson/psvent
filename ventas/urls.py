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
    path('cuentas-por-cobrar/', views.lista_cuentas_por_cobrar, name='lista_cuentas_por_cobrar'),
    path('cuenta/<int:cuenta_id>/', views.detalle_cuenta, name='detalle_cuenta'),
    path('cuenta/<int:cuenta_id>/pagar/', views.registrar_pago, name='registrar_pago'),
    path('pagos/', views.lista_pagos, name='lista_pagos'),
    path('pagos/<int:pago_id>/cancelar/', views.cancelar_pago, name='cancelar_pago'),
    
    path('pagos/<int:pago_id>/imprimir/<str:tipo>/', views.imprimir_recibo, name='imprimir_recibo_tipo'),
    path('pagos/<int:pago_id>/imprimir/', views.imprimir_recibo, name='imprimir_recibo'),
]