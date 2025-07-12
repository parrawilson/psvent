# facturacion/urls.py
from django.urls import path
from . import views

app_name = 'facturacion'

urlpatterns = [
    path('documentos/', views.lista_documentos, name='lista_documentos'),
    path('documentos/<int:documento_id>/', views.detalle_documento, name='detalle_documento'),
    path('ventas/<int:venta_id>/enviar-set/', views.enviar_set, name='enviar_set'),
    path('documentos/<int:documento_id>/reenviar/', views.reenviar_set, name='reenviar_set'),
    path('documentos/<int:documento_id>/xml/', views.descargar_xml, name='descargar_xml'),
]