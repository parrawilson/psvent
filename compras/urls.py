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
    

]