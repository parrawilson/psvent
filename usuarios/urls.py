from django.urls import path
from . import views


urlpatterns = [
    path('registro/', views.registro_usuario, name='registro'),
    path('login/', views.login_usuario, name='login'),
    path('perfil/', views.perfil_usuario, name='perfil'),
    path('editar/<int:usuario_id>/', views.editar_usuario, name='editar_usuario'),
    path('lista/', views.lista_usuarios, name='lista_usuarios'),
    path('logout/', views.logout_usuario, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard2/', views.dashboard2, name='dashboard2'),
]
