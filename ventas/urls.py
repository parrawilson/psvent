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

]