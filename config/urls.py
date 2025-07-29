"""
URL configuration for psvent project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('login', permanent=False)),
    path('empresa/', include('empresa.urls')), #rutas de empresa
    path('', include('usuarios.urls')),  # rutas de usuarios
    path('almacen/', include('almacen.urls')), #rutas de almacen
    path('compras/', include('compras.urls')), #rutas de compras
    path('caja/', include('caja.urls')), #rutas de compras
    path('ventas/', include('ventas.urls')), #rutas de compras
    path('facturacion/', include('facturacion.urls')), #rutas de facturacion
]
