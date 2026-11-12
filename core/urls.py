# core/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

urlpatterns = [
    # Dashboard y principal
    path('', views.dashboard, name='dashboard'),
    
    # Autenticación
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    
    # Perfil de usuario
    path('perfil/', views.perfil_usuario, name='perfil'),
    path('cambiar-password/', views.cambiar_password, name='cambiar_password'),
    
    # Gestión de usuarios (solo admin)
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    
    # Gestión de sedes
    path('sedes/', views.sedes, name='sedes'),
    
    # Gestión de dependencias
    path('dependencias/', views.dependencias, name='dependencias'),
]