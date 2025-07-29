from django.urls import path
from . import views

app_name = 'caja'

urlpatterns = [
    path('', views.lista_cajas, name='lista_cajas'),
    path('crear/', views.crear_caja, name='crear_caja'),
    path('<int:caja_id>/', views.detalle_caja, name='detalle_caja'),
    path('<int:caja_id>/abrir/', views.abrir_caja, name='abrir_caja'),
    path('<int:caja_id>/cerrar/', views.cerrar_caja, name='cerrar_caja'),
    path('<int:caja_id>/movimiento/', views.registrar_movimiento, name='registrar_movimiento'),
    path('<int:caja_id>/reporte-pdf/', views.reporte_cierre_pdf, name='reporte_cierre_pdf'),

    path('reportes/', views.reportes_caja, name='reportes_caja'),
    path('reportes/movimientos/', views.reporte_movimientos, name='reporte_movimientos'),
    path('reportes/cierres/', views.reporte_cierres, name='reporte_cierres'),
    path('reportes/sesion/<int:sesion_id>/pdf/', views.reporte_sesion_pdf, name='reporte_sesion_pdf'),

    path('api/caja/<int:caja_id>/punto-expedicion/', views.obtener_datos_caja, name='api_punto_expedicion'),

    
]