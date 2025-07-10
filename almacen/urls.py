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


    path('categorias/lista/', views.lista_categorias, name='lista_categorias'),
    path('categorias/nueva/', views.registrar_categoria, name='registrar_categoria'),
    path('categorias/editar/<int:categoria_id>/', views.editar_categoria, name='editar_categoria'),
    path('categorias/eliminar/<int:categoria_id>/', views.eliminar_categoria, name='eliminar_categoria'),


    path('unidades_medidas/lista/', views.lista_unidades_medidas, name='lista_unidades_medidas'),
    path('unidades_medidas/nueva/', views.registrar_unidad_medida, name='registrar_unidad_medida'),
    path('unidades_medidas/editar/<int:unidad_medida_id>/', views.editar_unidad_medida, name='editar_unidad_medida'),
    path('unidades_medidas/eliminar/<int:unidad_medida_id>/', views.eliminar_unidad_medida, name='eliminar_unidad_medida'),


    # Almacenes
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
]