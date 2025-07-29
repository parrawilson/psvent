from django.urls import path
from . import views
from .views import EmpresaUpdateView, SucursalListView, SucursalCreateView, SucursalUpdateView, PuntoExpedicionCreateView,PuntoExpedicionListView,PuntoExpedicionUpdateView,SecuenciaDocumentoUpdateView

app_name = 'empresa'

urlpatterns = [
    path('empresa/<int:pk>/', EmpresaUpdateView.as_view(), name='editar_empresa'),

    # Sucursales
    path('sucursales/', SucursalListView.as_view(), name='lista_sucursales'),
    path('sucursales/nueva/', SucursalCreateView.as_view(), name='crear_sucursal'),
    path('sucursales/<int:pk>/editar/', SucursalUpdateView.as_view(), name='editar_sucursal'),

    # Puntos de Expedición
    path('sucursales/<int:sucursal_id>/puntos/', PuntoExpedicionListView.as_view(), name='lista_puntos'),
    path('sucursales/<int:sucursal_id>/puntos/nuevo/', PuntoExpedicionCreateView.as_view(), name='crear_punto'),
    path('sucursales/<int:sucursal_id>/puntos/<int:pk>/editar/', PuntoExpedicionUpdateView.as_view(), name='editar_punto'),
    path('puntos/<int:pk>/secuencias/', views.SecuenciaDocumentoListView.as_view(), name='editar_secuencias'),
    path('secuencias/<int:pk>/editar/', views.SecuenciaDocumentoUpdateView.as_view(), name='editar_secuencia'),



    path('ajax/get-distritos/', views.get_distritos, name='get_distritos'),
    path('ajax/get-ciudades/', views.get_ciudades, name='get_ciudades'),
    path('ajax/get-barrios/', views.get_barrios, name='get_barrios'),



    # Actividades Económicas
    path('actividades/', views.ActividadEconomicaListView.as_view(), name='lista_actividades'),
    path('actividades/nueva/', views.ActividadEconomicaCreateView.as_view(), name='crear_actividad'),
    path('actividades/<int:pk>/editar/', views.ActividadEconomicaUpdateView.as_view(), name='editar_actividad'),
    #path('actividades/<int:pk>/eliminar/', views.ActividadEconomicaDeleteView.as_view(), name='eliminar_actividad'),
    #path('empresa/<int:pk>/actividades/', views.EmpresaActividadesView.as_view(), name='empresa_actividades'),
]
