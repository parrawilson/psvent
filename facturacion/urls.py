# facturacion/urls.py
from django.urls import path
from . import views

app_name = 'facturacion'

urlpatterns = [
    path('documentos/', views.lista_documentos, name='lista_documentos'),
    path('documentos/<int:documento_id>/', views.detalle_documento, name='detalle_documento'),
    path('documentos/<int:documento_id>/xml/', views.descargar_xml, name='descargar_xml'),
    path('ventas/<int:venta_id>/enviar-set/', views.enviar_set, name='enviar_set'),

    path('documento/<int:pk>/enviar/', views.enviar_documento_set, name='enviar_documento_set'),
    path('documento/<int:pk>/reenviar/', views.reenviar_documento_set, name='reenviar_documento_set'),

    path('documentos/<int:documento_id>/reenviar/', views.reenviar_set, name='reenviar_set'),
    

    path('documentos/<int:documento_id>/generar-kude/', views.generar_kude, name='generar_kude'),
    path('documentos/<int:documento_id>/kude/', views.descargar_kude, name='descargar_kude'),

    
]