from django.urls import path
from . import views


app_name= "compras"

urlpatterns = [
    
    # compras
    path('proveedores/', views.lista_proveedores, name='lista_proveedores'),
    path('proveedores/registrar/', views.registrar_proveedor, name='registrar_proveedor'),
    path('proveedores/editar/<int:proveedor_id>/', views.editar_proveedor, name='editar_proveedor'),
    path('proveedores/eliminar/<int:proveedor_id>/', views.eliminar_proveedor, name='eliminar_proveedor'),


    path('ordenes/', views.lista_ordenes_compra, name='lista_ordenes'),
    path('ordenes/nueva/', views.crear_orden_compra, name='crear_orden'),
    path('ordenes/<int:orden_id>/', views.detalle_orden_compra, name='detalle_orden'),
    path('ordenes/<int:orden_id>/editar/', views.editar_orden_compra, name='editar_orden'),
    path('ordenes/<int:orden_id>/aprobar/', views.aprobar_orden_compra, name='aprobar_orden'),
    path('ordenes/<int:orden_id>/recibir/', views.recibir_orden_compra, name='recibir_orden'),


    # Cuentas por Pagar
    path('cuentas-por-pagar/', views.lista_cuentas_por_pagar, name='lista_cuentas_por_pagar'),
    path('cuentas-por-pagar/<int:pk>/', views.detalle_cuenta_por_pagar, name='detalle_cuenta_por_pagar'),
    path('cuentas-por-pagar/<int:pk>/pagar/', views.registrar_pago_proveedor, name='registrar_pago_proveedor'),
    path('pagos-proveedor/<int:pk>/eliminar/', views.eliminar_pago_proveedor, name='eliminar_pago_proveedor'),
    

]