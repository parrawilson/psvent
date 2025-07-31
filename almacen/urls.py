from django.urls import path
from . import views
from . import api_views


app_name= "almacen"

urlpatterns = [
    path('productos/lista/', views.lista_productos, name='lista_productos'),
    path('productos/nueva/', views.registrar_producto, name='registrar_producto'),
    path('productos/editar/<int:producto_id>/', views.editar_producto, name='editar_producto'),
    path('productos/eliminar/<int:producto_id>/', views.eliminar_producto, name='eliminar_producto'),
    path('api/productos/buscar/', api_views.buscar_producto, name='buscar_producto'),
    path('api/productos/<int:pk>/', api_views.obtener_producto_por_id, name='detalle_producto'),

    path('servicios/lista/', views.lista_servicios, name='lista_servicios'),
    path('servicios/registrar/', views.registrar_servicio, name='registrar_servicio'),
    path('servicios/editar/<int:servicio_id>/', views.editar_servicio, name='editar_servicio'),
    path('servicios/eliminar/<int:servicio_id>/', views.eliminar_servicio, name='eliminar_servicio'),
    path('api/servicios/buscar/', api_views.buscar_servicio, name='buscar_servicio'),
    path('api/servicios/<int:pk>/', api_views.obtener_servicio_por_id, name='detalle_servicio'),

    path('api/buscar/', api_views.buscar_producto_servicio, name='buscar_producto_servicio'),
    path('api/almacenes/principal/', api_views.obtener_almacen_principal, name='obtener_almacen_principal'),


    path('categorias/lista/', views.lista_categorias, name='lista_categorias'),
    path('categorias/nueva/', views.registrar_categoria, name='registrar_categoria'),
    path('categorias/editar/<int:categoria_id>/', views.editar_categoria, name='editar_categoria'),
    path('categorias/eliminar/<int:categoria_id>/', views.eliminar_categoria, name='eliminar_categoria'),


    path('unidades_medidas/lista/', views.lista_unidades_medidas, name='lista_unidades_medidas'),
    path('unidades_medidas/nueva/', views.registrar_unidad_medida, name='registrar_unidad_medida'),
    path('unidades_medidas/editar/<int:unidad_medida_id>/', views.editar_unidad_medida, name='editar_unidad_medida'),
    path('unidades_medidas/eliminar/<int:unidad_medida_id>/', views.eliminar_unidad_medida, name='eliminar_unidad_medida'),


    # Almacenes
    path('almacenes/menu/', views.menu_almacenes, name='menu_almacenes'),
    path('almacenes/', views.lista_almacenes, name='lista_almacenes'),
    path('almacenes/registrar/', views.registrar_almacen, name='registrar_almacen'),
    path('almacenes/editar/<int:almacen_id>/', views.editar_almacen, name='editar_almacen'),
    path('almacenes/eliminar/<int:almacen_id>/', views.eliminar_almacen, name='eliminar_almacen'),
    
    # Movimientos
    path('movimientos/', views.lista_movimientos, name='lista_movimientos'),
    path('movimientos/registrar/', views.registrar_movimiento, name='registrar_movimiento'),
    path('movimientos/editar/<int:movimiento_id>/', views.editar_movimiento, name='editar_movimiento'),
    path('movimientos/eliminar/<int:movimiento_id>/', views.eliminar_movimiento, name='eliminar_movimiento'),
    
    # Stock
    path('stock/', views.lista_stock, name='lista_stock'),
    path('inventario/', views.lista_inventarios, name='inventario'),
    path('reportes/', views.lista_reportes, name='reportes'),


    # Tipos de Conversión
    path('conversiones/tipos/', views.lista_tipos_conversion, name='lista_tipos_conversion'),
    path('conversiones/tipos/nuevo/', views.crear_tipo_conversion, name='crear_tipo_conversion'),
    path('conversiones/tipos/editar/<int:tipo_conversion_id>/', views.editar_tipo_conversion, name='editar_tipo_conversion'),
    path('conversiones/tipos/eliminar/<int:tipo_conversion_id>/', views.eliminar_tipo_conversion, name='eliminar_tipo_conversion'),

    # Configuración de Conversiones
    path('conversiones/menu/', views.menu_conversiones, name='menu_conversiones'),
    path('conversiones/', views.lista_conversiones, name='lista_conversiones'),
    path('conversiones/nueva/', views.crear_conversion, name='crear_conversion'),
    path('conversiones/editar/<int:conversion_id>/', views.editar_conversion, name='editar_conversion'),
    path('conversiones/activar/<int:conversion_id>/', views.activar_conversion, name='activar_conversion'),
    path('conversiones/desactivar/<int:conversion_id>/', views.desactivar_conversion, name='desactivar_conversion'),
    
    # Ejecución de Conversiones
    path('conversiones/ejecutar/', views.ejecutar_conversion, name='ejecutar_conversion'),
    path('conversiones/historial/', views.historial_conversiones, name='historial_conversiones'),
    path('conversiones/revertir/<int:registro_id>/', views.revertir_conversion_view, name='revertir_conversion'),
    
    # API Endpoints (para AJAX)
    path('api/conversion/<int:pk>/', views.api_detalle_conversion, name='api_detalle_conversion'),


    # Traslados entre almacenes
    path('traslados/', views.listar_traslados, name='lista_traslados'),
    path('traslados/nuevo/', views.crear_traslado, name='crear_traslado'),
    path('traslados/<int:traslado_id>/', views.detalle_traslado, name='detalle_traslado'),
    path('traslados/<int:traslado_id>/procesar/', views.procesar_traslado, name='procesar_traslado'),
    path('traslados/<int:traslado_id>/recibir/', views.recibir_traslado, name='recibir_traslado'),


]