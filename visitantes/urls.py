# visitantes/urls.py
from django.urls import path
from . import views

app_name = 'visitantes'

urlpatterns = [
    path('registrar/', views.registrar_visitante, name='registrar'),
    path('registro-exitoso/<int:registro_id>/', views.registro_exitoso, name='registro_exitoso'),
    path('devolver/', views.devolver_carnet, name='devolver'),
    path('activas/', views.visitas_activas, name='visitas_activas'),
    path('historial/', views.historial_visitas, name='historial'),
    path('buscar/', views.buscar_visitante, name='buscar_visitante'),
    path('carnets-faltantes/', views.carnets_faltantes, name='carnets_faltantes'),
    path('lista/', views.lista_visitantes, name='lista_visitantes'),
]